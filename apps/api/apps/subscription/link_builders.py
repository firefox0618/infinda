import base64
import json
from urllib.parse import urlencode

from django.conf import settings


HAPP_ANDROID_APK_URL = (
    "https://github.com/Happ-proxy/happ-android/releases/latest/download/Happ.apk"
)
HAPP_WINDOWS_SETUP_URL = (
    "https://github.com/Happ-proxy/happ-desktop/releases/latest/download/setup-Happ.x64.exe"
)
HAPP_LINUX_X64_DEB_URL = (
    "https://github.com/Happ-proxy/happ-desktop/releases/latest/download/Happ.linux.x64.deb"
)
HAPP_LINUX_ARM64_DEB_URL = (
    "https://github.com/Happ-proxy/happ-desktop/releases/latest/download/Happ.linux.arm64.deb"
)
HAPP_LINUX_X64_RPM_URL = (
    "https://github.com/Happ-proxy/happ-desktop/releases/latest/download/Happ.linux.x64.rpm"
)
HAPP_LINUX_ARM64_RPM_URL = (
    "https://github.com/Happ-proxy/happ-desktop/releases/latest/download/Happ.linux.arm64.rpm"
)
HAPP_LINUX_X64_ARCH_URL = (
    "https://github.com/Happ-proxy/happ-desktop/releases/latest/download/Happ.linux.x64.pkg.tar.zst"
)
HAPP_LINUX_ARM64_ARCH_URL = (
    "https://github.com/Happ-proxy/happ-desktop/releases/latest/download/Happ.linux.arm64.pkg.tar.zst"
)
HAPP_ANDROID_STORE_URL = "https://play.google.com/store/apps/details?id=com.happproxy"
HAPP_IOS_RU_STORE_URL = "https://apps.apple.com/ru/app/happ-proxy-utility-plus/id6746188973"
HAPP_IOS_GLOBAL_STORE_URL = "https://apps.apple.com/us/app/happ-proxy-utility/id6504287215"
HAPP_APPLE_TV_STORE_URL = "https://apps.apple.com/us/app/happ-proxy-utility-for-tv/id6748297274"


def get_public_web_base_url() -> str:
    return str(getattr(settings, "PUBLIC_WEB_BASE_URL", "http://localhost:3000")).rstrip("/")


def build_public_subscription_page_url(*, token: str) -> str:
    return f"{get_public_web_base_url()}/sub/{str(token).strip()}"


def build_public_subscription_feed_url(*, token: str) -> str:
    return f"{build_public_subscription_page_url(token=token)}/feed"


def build_public_subscription_happ_wrapper_url(*, token: str) -> str:
    query = urlencode({"sub": build_public_subscription_feed_url(token=token)})
    return f"{get_public_web_base_url()}/happ/add?{query}"


def build_public_subscription_happ_deep_link(*, token: str) -> str:
    return f"happ://add/{build_public_subscription_feed_url(token=token)}"


def build_public_subscription_happ_routing_profile() -> dict[str, object]:
    profile_name = str(getattr(settings, "PUBLIC_HAPP_PROFILE_NAME", "INFINDA")).strip() or "INFINDA"
    return {
        "Name": profile_name,
        "GlobalProxy": "true",
        "RemoteDNSType": "DoH",
        "RemoteDNSDomain": "https://cloudflare-dns.com/dns-query",
        "RemoteDNSIP": "1.1.1.1",
        "DomesticDNSType": "DoH",
        "DomesticDNSDomain": "https://dns.google/dns-query",
        "DomesticDNSIP": "8.8.8.8",
        "Geoipurl": "https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geoip.dat",
        "Geositeurl": "https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geosite.dat",
        "DnsHosts": {
            "cloudflare-dns.com": "1.1.1.1",
            "dns.google": "8.8.8.8",
        },
        "DirectSites": ["geosite:private"],
        "DirectIp": [
            "geoip:private",
            "10.0.0.0/8",
            "172.16.0.0/12",
            "192.168.0.0/16",
            "169.254.0.0/16",
            "224.0.0.0/4",
            "255.255.255.255",
        ],
        "ProxySites": [],
        "ProxyIp": [],
        "BlockSites": ["geosite:category-ads-all"],
        "BlockIp": [],
        "DomainStrategy": "IPIfNonMatch",
        "FakeDNS": "false",
    }


def build_public_subscription_happ_routing_link() -> str:
    raw_json = json.dumps(
        build_public_subscription_happ_routing_profile(),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    encoded = base64.b64encode(raw_json.encode("utf-8")).decode("ascii")
    return f"happ://routing/onadd/{encoded}"


def build_public_subscription_client_links(*, token: str) -> list[dict[str, str]]:
    return [
        {
            "code": "happ",
            "label": "Открыть Happ",
            "kind": "happ",
            "url": build_public_subscription_happ_wrapper_url(token=token),
        },
        {
            "code": "generic",
            "label": "Другие клиенты",
            "kind": "generic",
            "url": build_public_subscription_feed_url(token=token),
        },
        {
            "code": "happ_routing",
            "label": "Настройки Happ",
            "kind": "routing",
            "url": build_public_subscription_happ_routing_link(),
        },
    ]


def build_public_subscription_install_guides() -> list[dict[str, object]]:
    return [
        {
            "code": "android",
            "title": "Android",
            "description": (
                "Установите Happ из Google Play. Если магазин недоступен, используйте APK и затем "
                "вернитесь к этой странице, чтобы открыть feed в приложении."
            ),
            "links": [
                {"label": "Google Play", "url": HAPP_ANDROID_STORE_URL},
                {"label": "Скачать APK", "url": HAPP_ANDROID_APK_URL},
            ],
        },
        {
            "code": "ios",
            "title": "iPhone и iPad",
            "description": (
                "Установите Happ из App Store. После первого запуска подтвердите системный профиль "
                "подключения и вернитесь к подписке."
            ),
            "links": [
                {"label": "App Store (RU)", "url": HAPP_IOS_RU_STORE_URL},
                {"label": "App Store (Global)", "url": HAPP_IOS_GLOBAL_STORE_URL},
            ],
        },
        {
            "code": "windows",
            "title": "Windows",
            "description": (
                "Скачайте установщик Happ для Windows, завершите установку и затем импортируйте "
                "подписку через feed или прямое открытие."
            ),
            "links": [
                {"label": "Windows x64", "url": HAPP_WINDOWS_SETUP_URL},
            ],
        },
        {
            "code": "macos",
            "title": "macOS",
            "description": (
                "Установите Happ из App Store и подтвердите системный запрос на добавление профиля "
                "подключения, если macOS его покажет."
            ),
            "links": [
                {"label": "App Store (RU)", "url": HAPP_IOS_RU_STORE_URL},
                {"label": "App Store (Global)", "url": HAPP_IOS_GLOBAL_STORE_URL},
            ],
        },
        {
            "code": "linux",
            "title": "Linux",
            "description": (
                "Выберите пакет под свой дистрибутив и архитектуру, установите Happ, затем вернитесь "
                "к странице подписки и откройте feed вручную."
            ),
            "links": [
                {"label": "x64 .deb", "url": HAPP_LINUX_X64_DEB_URL},
                {"label": "arm64 .deb", "url": HAPP_LINUX_ARM64_DEB_URL},
                {"label": "x64 .rpm", "url": HAPP_LINUX_X64_RPM_URL},
                {"label": "arm64 .rpm", "url": HAPP_LINUX_ARM64_RPM_URL},
                {"label": "x64 Arch", "url": HAPP_LINUX_X64_ARCH_URL},
                {"label": "arm64 Arch", "url": HAPP_LINUX_ARM64_ARCH_URL},
            ],
        },
        {
            "code": "apple_tv",
            "title": "Apple TV",
            "description": (
                "Откройте страницу Happ в App Store на Apple TV, установите приложение и затем "
                "вернитесь к подписке на основном устройстве для импорта ссылки."
            ),
            "links": [
                {"label": "App Store", "url": HAPP_APPLE_TV_STORE_URL},
            ],
        },
        {
            "code": "android_tv",
            "title": "Android TV",
            "description": (
                "Установите Happ из Google Play или через APK. После установки откройте feed из этой "
                "подписки на устройстве, где будете импортировать конфиг."
            ),
            "links": [
                {"label": "Google Play", "url": HAPP_ANDROID_STORE_URL},
                {"label": "Скачать APK", "url": HAPP_ANDROID_APK_URL},
            ],
        },
    ]


def build_client_links_for_source_url(*, source_url: str, code_prefix: str) -> list[dict[str, str]]:
    normalized_source_url = str(source_url).strip()
    query = urlencode({"sub": normalized_source_url})
    return [
        {
            "code": f"{code_prefix}_happ",
            "label": "Happ для сервера",
            "kind": "happ",
            "url": f"{get_public_web_base_url()}/happ/add?{query}",
        },
        {
            "code": f"{code_prefix}_generic",
            "label": "Другие клиенты",
            "kind": "generic",
            "url": normalized_source_url,
        },
    ]
