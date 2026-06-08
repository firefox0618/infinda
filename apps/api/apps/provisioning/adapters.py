import json
import time
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote

import httpx
from django.conf import settings

from .models import ProvisionedDeviceAccess, ProvisioningOperation, ServerProvisioningProfile


class ProvisioningAdapterError(Exception):
    def __init__(self, *, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class ProvisioningHealthCheckResult:
    adapter: str
    is_available: bool
    latency_ms: int | None
    error_code: str
    error_message: str
    details: dict


@dataclass(frozen=True)
class ProvisioningBindingResult:
    adapter: str
    result_payload: dict
    external_client_uuid: str
    external_client_email: str
    external_client_id: str
    inbound_id: int
    connection_url: str
    metadata: dict


class BaseProvisioningAdapter:
    adapter_code = "base"

    def __init__(self, profile: ServerProvisioningProfile):
        self.profile = profile

    def health_check(self) -> ProvisioningHealthCheckResult:
        raise NotImplementedError

    def sync_binding(
        self,
        *,
        binding: ProvisionedDeviceAccess,
        access_expires_at: datetime | None,
        operation: ProvisioningOperation,
    ) -> ProvisioningBindingResult:
        raise NotImplementedError

    def revoke_binding(
        self,
        *,
        binding: ProvisionedDeviceAccess,
        operation: ProvisioningOperation,
    ):
        raise NotImplementedError


class MockProvisioningAdapter(BaseProvisioningAdapter):
    adapter_code = ServerProvisioningProfile.Adapter.MOCK

    def health_check(self) -> ProvisioningHealthCheckResult:
        return ProvisioningHealthCheckResult(
            adapter=self.adapter_code,
            is_available=True,
            latency_ms=0,
            error_code="",
            error_message="",
            details={"mode": "mock"},
        )

    def sync_binding(
        self,
        *,
        binding: ProvisionedDeviceAccess,
        access_expires_at: datetime | None,
        operation: ProvisioningOperation,
    ) -> ProvisioningBindingResult:
        external_client_uuid = binding.external_client_uuid or f"mock-device-{binding.device_id}"
        external_client_email = binding.external_client_email or (
            f"infinda-s{binding.subscription_id or 0}-d{binding.device_id}-{binding.route.code}@mock.local"
        )
        return ProvisioningBindingResult(
            adapter=self.adapter_code,
            result_payload={
                "mode": "mock-binding-synced",
                "operation_type": operation.operation_type,
                "route_code": binding.route.code,
                "server_code": binding.server.code,
                "device_id": binding.device_id,
                "expires_at": access_expires_at.isoformat() if access_expires_at else None,
            },
            external_client_uuid=external_client_uuid,
            external_client_email=external_client_email,
            external_client_id=external_client_uuid,
            inbound_id=int(binding.inbound_id or 0),
            connection_url=binding.connection_url or binding.route.endpoint_url,
            metadata={"mode": "mock", "route_code": binding.route.code},
        )

    def revoke_binding(
        self,
        *,
        binding: ProvisionedDeviceAccess,
        operation: ProvisioningOperation,
    ) -> dict:
        return {
            "adapter": self.adapter_code,
            "result_payload": {
                "mode": "mock-binding-revoked",
                "operation_type": operation.operation_type,
                "route_code": binding.route.code,
                "server_code": binding.server.code,
                "device_id": binding.device_id,
            },
        }


class XuiProvisioningAdapter(BaseProvisioningAdapter):
    adapter_code = ServerProvisioningProfile.Adapter.XUI

    def _resolve_username(self) -> str:
        return self.profile.panel_username.strip() or str(
            getattr(settings, "PROVISIONING_XUI_DEFAULT_USERNAME", "")
        ).strip()

    def _resolve_password(self) -> str:
        return self.profile.panel_password.strip() or str(
            getattr(settings, "PROVISIONING_XUI_DEFAULT_PASSWORD", "")
        ).strip()

    def _resolve_timeout(self) -> float:
        profile_timeout = self.profile.request_timeout_seconds
        if profile_timeout and profile_timeout > 0:
            return float(profile_timeout)
        return float(getattr(settings, "PROVISIONING_XUI_REQUEST_TIMEOUT_SECONDS", 15))

    def _resolve_verify_tls(self) -> bool:
        return bool(
            self.profile.verify_tls
            if self.profile.verify_tls is not None
            else getattr(settings, "PROVISIONING_XUI_VERIFY_TLS", True)
        )

    def _build_client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self.profile.panel_base_url.rstrip("/"),
            follow_redirects=True,
            timeout=self._resolve_timeout(),
            verify=self._resolve_verify_tls(),
        )

    def _authenticate(self, client: httpx.Client) -> None:
        base_url = self.profile.panel_base_url.strip()
        username = self._resolve_username()
        password = self._resolve_password()
        if not base_url or not username or not password:
            raise ProvisioningAdapterError(
                code="XUI_CONFIG_INCOMPLETE",
                message="XUI provisioning profile is incomplete.",
            )

        login_response = client.post(
            "/login",
            data={"username": username, "password": password},
        )
        if login_response.status_code != 200:
            raise ProvisioningAdapterError(
                code="XUI_LOGIN_FAILED",
                message="XUI login failed.",
            )

    def _get_inbounds_payload(self, client: httpx.Client) -> dict:
        response = client.get("/panel/api/inbounds/list")
        response.raise_for_status()
        return response.json()

    def _resolve_inbound(self, payload: dict) -> dict:
        if not payload.get("success"):
            raise ProvisioningAdapterError(
                code="XUI_INBOUNDS_UNAVAILABLE",
                message="XUI panel returned unsuccessful inbound response.",
            )

        inbounds = payload.get("obj") or []
        if not isinstance(inbounds, list) or not inbounds:
            raise ProvisioningAdapterError(
                code="XUI_INBOUND_NOT_FOUND",
                message="No inbounds available in XUI panel.",
            )

        configured_inbound_id = int(self.profile.default_inbound_id or 0)
        if configured_inbound_id > 0:
            for inbound in inbounds:
                if int(inbound.get("id") or 0) == configured_inbound_id:
                    return inbound
            raise ProvisioningAdapterError(
                code="XUI_INBOUND_NOT_FOUND",
                message="Configured inbound id is missing in XUI panel.",
            )

        for inbound in inbounds:
            if str(inbound.get("protocol") or "").strip().lower() == "vless" and int(
                inbound.get("port") or 0
            ) == 443:
                return inbound

        for inbound in inbounds:
            if str(inbound.get("protocol") or "").strip().lower() == "vless":
                return inbound

        raise ProvisioningAdapterError(
            code="XUI_INBOUND_NOT_FOUND",
            message="No VLESS inbound found in XUI panel.",
        )

    @staticmethod
    def _build_vless_client_settings(
        *,
        client_uuid: str,
        email: str,
        expiry_time_ms: int,
        enable: bool,
    ) -> dict:
        return {
            "clients": [
                {
                    "id": client_uuid,
                    "flow": "",
                    "email": email,
                    "limitIp": 1,
                    "totalGB": 0,
                    "expiryTime": expiry_time_ms,
                    "enable": enable,
                    "tgId": 0,
                    "subId": "",
                    "comment": "",
                    "reset": 0,
                }
            ]
        }

    @staticmethod
    def _extract_reality_value(reality_settings: dict, key: str) -> str:
        direct_value = reality_settings.get(key)
        if isinstance(direct_value, str) and direct_value.strip():
            return direct_value.strip()
        settings_value = reality_settings.get("settings") or {}
        candidate = settings_value.get(key)
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
        if isinstance(candidate, list):
            for item in candidate:
                if str(item).strip():
                    return str(item).strip()
        return ""

    def _build_vless_connection_url(self, *, inbound: dict, client_uuid: str, email: str) -> str:
        stream_settings = inbound.get("streamSettings")
        if isinstance(stream_settings, str):
            try:
                stream_settings = json.loads(stream_settings)
            except json.JSONDecodeError:
                stream_settings = {}
        stream_settings = stream_settings if isinstance(stream_settings, dict) else {}
        reality_settings = stream_settings.get("realitySettings") or {}
        network = str(stream_settings.get("network") or "tcp").strip() or "tcp"
        security = str(stream_settings.get("security") or "reality").strip() or "reality"
        host = httpx.URL(self.profile.panel_base_url).host or self.profile.server.hostname
        port = int(inbound.get("port") or 443)
        public_key = self._extract_reality_value(reality_settings, "publicKey")
        fingerprint = self._extract_reality_value(reality_settings, "fingerprint") or "chrome"
        server_name = self._extract_reality_value(reality_settings, "serverNames")
        short_id = self._extract_reality_value(reality_settings, "shortIds")
        path = ""
        transport_settings = stream_settings.get(f"{network}Settings") or {}
        if isinstance(transport_settings, dict):
            path = str(transport_settings.get("path") or transport_settings.get("serviceName") or "").strip()

        query = {
            "type": network,
            "security": security,
            "fp": fingerprint,
        }
        if public_key:
            query["pbk"] = public_key
        if server_name:
            query["sni"] = server_name
        if short_id:
            query["sid"] = short_id
        if path:
            query["path"] = path

        query_string = "&".join(
            f"{quote(str(key), safe='')}={quote(str(value), safe='')}"
            for key, value in query.items()
            if str(value).strip()
        )
        return f"vless://{client_uuid}@{host}:{port}?{query_string}#{quote(email, safe='')}"

    def _add_client(
        self,
        *,
        client: httpx.Client,
        inbound_id: int,
        client_uuid: str,
        email: str,
        expiry_time_ms: int,
    ) -> dict:
        payload = {
            "id": inbound_id,
            "settings": json.dumps(
                self._build_vless_client_settings(
                    client_uuid=client_uuid,
                    email=email,
                    expiry_time_ms=expiry_time_ms,
                    enable=True,
                )
            ),
        }
        try:
            response = client.post("/panel/api/inbounds/addClient", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code != 404:
                raise

        response = client.post(
            "/panel/api/clients/add",
            json={
                "client": self._build_vless_client_settings(
                    client_uuid=client_uuid,
                    email=email,
                    expiry_time_ms=expiry_time_ms,
                    enable=True,
                )["clients"][0],
                "inboundIds": [inbound_id],
            },
        )
        response.raise_for_status()
        return response.json()

    def _update_client(
        self,
        *,
        client: httpx.Client,
        inbound_id: int,
        client_uuid: str,
        email: str,
        expiry_time_ms: int,
        enable: bool,
    ) -> dict:
        payload = {
            "id": inbound_id,
            "settings": json.dumps(
                self._build_vless_client_settings(
                    client_uuid=client_uuid,
                    email=email,
                    expiry_time_ms=expiry_time_ms,
                    enable=enable,
                )
            ),
        }
        try:
            response = client.post(
                f"/panel/api/inbounds/updateClient/{quote(client_uuid, safe='')}",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code != 404:
                raise

        response = client.post(
            f"/panel/api/clients/update/{quote(email, safe='')}",
            json=self._build_vless_client_settings(
                client_uuid=client_uuid,
                email=email,
                expiry_time_ms=expiry_time_ms,
                enable=enable,
            )["clients"][0],
        )
        response.raise_for_status()
        return response.json()

    def _delete_client(self, *, client: httpx.Client, email: str) -> dict:
        response = client.post(f"/panel/api/clients/del/{quote(email, safe='')}")
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _assert_success(*, payload: dict, code: str, message: str) -> None:
        if payload.get("success", True):
            return
        raise ProvisioningAdapterError(code=code, message=message)

    def health_check(self) -> ProvisioningHealthCheckResult:
        started_at = time.monotonic()
        with self._build_client() as client:
            self._authenticate(client)
            inbound = self._resolve_inbound(self._get_inbounds_payload(client))
        latency_ms = max(int((time.monotonic() - started_at) * 1000), 1)
        return ProvisioningHealthCheckResult(
            adapter=self.adapter_code,
            is_available=True,
            latency_ms=latency_ms,
            error_code="",
            error_message="",
            details={
                "panel_base_url": self.profile.panel_base_url.rstrip("/"),
                "inbound_id": int(inbound.get("id") or 0),
                "inbound_protocol": str(inbound.get("protocol") or ""),
                "inbound_port": int(inbound.get("port") or 0),
            },
        )

    def sync_binding(
        self,
        *,
        binding: ProvisionedDeviceAccess,
        access_expires_at: datetime | None,
        operation: ProvisioningOperation,
    ) -> ProvisioningBindingResult:
        if access_expires_at is None:
            raise ProvisioningAdapterError(
                code="ACCESS_EXPIRY_REQUIRED",
                message="Access expiry is required for XUI sync.",
            )

        expiry_time_ms = int(access_expires_at.timestamp() * 1000)
        with self._build_client() as client:
            self._authenticate(client)
            inbound = self._resolve_inbound(self._get_inbounds_payload(client))
            inbound_id = int(inbound.get("id") or 0)
            if binding.external_client_uuid and binding.external_client_email:
                payload = self._update_client(
                    client=client,
                    inbound_id=inbound_id,
                    client_uuid=binding.external_client_uuid,
                    email=binding.external_client_email,
                    expiry_time_ms=expiry_time_ms,
                    enable=True,
                )
                self._assert_success(
                    payload=payload,
                    code="XUI_UPDATE_FAILED",
                    message="XUI failed to update client.",
                )
                external_client_uuid = binding.external_client_uuid
                external_client_email = binding.external_client_email
            else:
                payload = self._add_client(
                    client=client,
                    inbound_id=inbound_id,
                    client_uuid=binding.external_client_uuid,
                    email=binding.external_client_email,
                    expiry_time_ms=expiry_time_ms,
                )
                self._assert_success(
                    payload=payload,
                    code="XUI_ADD_FAILED",
                    message="XUI failed to create client.",
                )
                external_client_uuid = binding.external_client_uuid
                external_client_email = binding.external_client_email

        return ProvisioningBindingResult(
            adapter=self.adapter_code,
            result_payload={
                "mode": "xui-binding-synced",
                "operation_type": operation.operation_type,
                "route_code": binding.route.code,
                "server_code": binding.server.code,
                "device_id": binding.device_id,
                "inbound_id": inbound_id,
            },
            external_client_uuid=external_client_uuid,
            external_client_email=external_client_email,
            external_client_id=external_client_email,
            inbound_id=inbound_id,
            connection_url=self._build_vless_connection_url(
                inbound=inbound,
                client_uuid=external_client_uuid,
                email=external_client_email,
            ),
            metadata={
                "provider_type": self.adapter_code,
                "panel_base_url": self.profile.panel_base_url.rstrip("/"),
                "route_code": binding.route.code,
                "device_id": binding.device_id,
            },
        )

    def revoke_binding(
        self,
        *,
        binding: ProvisionedDeviceAccess,
        operation: ProvisioningOperation,
    ) -> dict:
        if not binding.external_client_email:
            raise ProvisioningAdapterError(
                code="MISSING_EXTERNAL_CLIENT_EMAIL",
                message="Provisioned binding is missing external client email.",
            )

        with self._build_client() as client:
            self._authenticate(client)
            payload = self._delete_client(client=client, email=binding.external_client_email)
            self._assert_success(
                payload=payload,
                code="XUI_DELETE_FAILED",
                message="XUI failed to delete client.",
            )

        return {
            "adapter": self.adapter_code,
            "result_payload": {
                "mode": "xui-binding-revoked",
                "operation_type": operation.operation_type,
                "route_code": binding.route.code,
                "server_code": binding.server.code,
                "device_id": binding.device_id,
                "external_client_email": binding.external_client_email,
            },
        }


class ManualProvisioningAdapter(BaseProvisioningAdapter):
    adapter_code = ServerProvisioningProfile.Adapter.MANUAL

    def health_check(self) -> ProvisioningHealthCheckResult:
        return ProvisioningHealthCheckResult(
            adapter=self.adapter_code,
            is_available=True,
            latency_ms=None,
            error_code="",
            error_message="",
            details={"mode": "manual", "notes": self.profile.notes},
        )

    def sync_binding(
        self,
        *,
        binding: ProvisionedDeviceAccess,
        access_expires_at: datetime | None,
        operation: ProvisioningOperation,
    ) -> ProvisioningBindingResult:
        external_client_uuid = binding.external_client_uuid or f"manual-device-{binding.device_id}"
        external_client_email = binding.external_client_email or (
            f"infinda-s{binding.subscription_id or 0}-d{binding.device_id}-{binding.route.code}@manual.local"
        )
        return ProvisioningBindingResult(
            adapter=self.adapter_code,
            result_payload={
                "mode": "manual-binding-pending",
                "operation_type": operation.operation_type,
                "device_id": binding.device_id,
                "route_code": binding.route.code,
                "notes": self.profile.notes,
                "expires_at": access_expires_at.isoformat() if access_expires_at else None,
            },
            external_client_uuid=external_client_uuid,
            external_client_email=external_client_email,
            external_client_id=external_client_email,
            inbound_id=int(binding.inbound_id or 0),
            connection_url=binding.connection_url,
            metadata={"mode": "manual", "notes": self.profile.notes},
        )

    def revoke_binding(
        self,
        *,
        binding: ProvisionedDeviceAccess,
        operation: ProvisioningOperation,
    ) -> dict:
        return {
            "adapter": self.adapter_code,
            "result_payload": {
                "mode": "manual-binding-revoked",
                "operation_type": operation.operation_type,
                "device_id": binding.device_id,
                "route_code": binding.route.code,
                "notes": self.profile.notes,
            },
        }


def resolve_provisioning_adapter(*, profile: ServerProvisioningProfile) -> BaseProvisioningAdapter:
    if profile.adapter == ServerProvisioningProfile.Adapter.XUI:
        return XuiProvisioningAdapter(profile)
    if profile.adapter == ServerProvisioningProfile.Adapter.MANUAL:
        return ManualProvisioningAdapter(profile)
    return MockProvisioningAdapter(profile)
