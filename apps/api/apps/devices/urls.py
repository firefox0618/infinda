from django.urls import path

from .views import DeviceListView, DeviceRevokeView


urlpatterns = [
    path("", DeviceListView.as_view(), name="device-list"),
    path("<int:device_id>/revoke/", DeviceRevokeView.as_view(), name="device-revoke"),
]
