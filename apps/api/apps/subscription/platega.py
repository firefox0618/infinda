import json
from dataclasses import dataclass
from typing import Any

import httpx
from django.conf import settings


class PlategaError(RuntimeError):
    pass


@dataclass(frozen=True)
class PlategaPayment:
    transaction_id: str
    checkout_url: str
    status: str
    payment_method_id: int | str
    raw: dict[str, Any]


class PlategaClient:
    METHOD_SBP_QR = 2

    STATUS_PENDING = "PENDING"
    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_CANCELED = "CANCELED"
    STATUS_CHARGEBACKED = "CHARGEBACKED"

    def __init__(
        self,
        merchant_id: str | None = None,
        secret_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.merchant_id = (
            merchant_id if merchant_id is not None else settings.PLATEGA_MERCHANT_ID
        )
        self.secret_key = (
            secret_key if secret_key is not None else settings.PLATEGA_SECRET_KEY
        )
        self.base_url = (
            base_url if base_url is not None else settings.PLATEGA_BASE_URL
        ).rstrip("/")

    @property
    def configured(self) -> bool:
        return bool(self.merchant_id and self.secret_key)

    def _headers(self) -> dict[str, str]:
        if not self.configured:
            raise PlategaError("Platega merchant credentials are not configured")

        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-MerchantId": str(self.merchant_id),
            "X-Secret": str(self.secret_key),
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        json_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            response = client.request(
                method,
                f"{self.base_url}{endpoint}",
                headers=self._headers(),
                json=json_payload,
            )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            try:
                details = response.json()
            except ValueError:
                details = response.text
            raise PlategaError(f"Platega request failed: {details}") from exc

        try:
            return response.json()
        except ValueError as exc:
            raise PlategaError("Platega returned invalid JSON") from exc

    def create_payment(
        self,
        *,
        amount_rub: int,
        description: str,
        payload: dict[str, Any],
        return_url: str | None = None,
        failed_url: str | None = None,
    ) -> PlategaPayment:
        response = self._request(
            "POST",
            "/transaction/process",
            json_payload={
                "paymentMethod": self.METHOD_SBP_QR,
                "paymentDetails": {
                    "amount": float(amount_rub),
                    "currency": "RUB",
                },
                "description": description,
                "payload": json.dumps(
                    payload,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                **({"return": return_url} if return_url else {}),
                **({"failedUrl": failed_url} if failed_url else {}),
            },
        )

        transaction_id = str(response.get("transactionId") or "").strip()
        checkout_url = str(response.get("redirect") or "").strip()
        if not transaction_id or not checkout_url:
            raise PlategaError("Platega did not return transactionId or redirect URL")

        return PlategaPayment(
            transaction_id=transaction_id,
            checkout_url=checkout_url,
            status=str(response.get("status") or self.STATUS_PENDING),
            payment_method_id=response.get("paymentMethod") or self.METHOD_SBP_QR,
            raw=response,
        )

    def validate_callback(self, *, headers: dict[str, str], body: bytes) -> dict[str, Any]:
        if not self.configured:
            raise PlategaError("Platega merchant credentials are not configured")

        normalized_headers = {key.lower(): value for key, value in headers.items()}
        merchant_id = normalized_headers.get("x-merchantid") or normalized_headers.get(
            "x-merchant-id"
        )
        secret = normalized_headers.get("x-secret")
        if merchant_id != self.merchant_id:
            raise PlategaError("Invalid or missing X-MerchantId header")
        if secret != self.secret_key:
            raise PlategaError("Invalid or missing X-Secret header")
        if not body:
            raise PlategaError("Empty callback body")

        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PlategaError("Invalid callback JSON") from exc

        required_fields = {"id", "status", "paymentMethod"}
        missing = [field for field in required_fields if field not in payload]
        if missing:
            raise PlategaError(f"Missing callback fields: {', '.join(missing)}")

        return payload

    @staticmethod
    def parse_payload(raw_payload: str | None) -> dict[str, Any]:
        if not raw_payload:
            raise PlategaError("Payment payload is empty")

        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError as exc:
            raise PlategaError("Payment payload is invalid") from exc

        if not isinstance(payload, dict):
            raise PlategaError("Payment payload is not an object")

        return payload
