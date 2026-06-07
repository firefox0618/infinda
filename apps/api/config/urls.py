from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from .admin_dashboard import configure_admin_site


configure_admin_site(admin.site)

admin.site.site_header = "INFINDA — администрирование"
admin.site.site_title = "INFINDA admin"
admin.site.index_title = "Управление данными и доступом"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.auth.urls")),
    path("api/profile/", include("apps.profile.urls")),
    path("api/devices/", include("apps.devices.urls")),
    path("api/access/", include("apps.access.urls")),
    path("api/subscription/", include("apps.subscription.urls")),
    path("api/support/", include("apps.support.urls")),
    path("api/telegram/", include("apps.telegram.urls")),
    path("api/", include("apps.health.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
