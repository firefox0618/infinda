from django.contrib import admin
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
    path("api/subscription/", include("apps.subscription.urls")),
    path("api/", include("apps.health.urls")),
]
