from django.urls import path

from .views import CurrentAccessStateView, CurrentAccessSyncView


urlpatterns = [
    path("", CurrentAccessStateView.as_view(), name="current-access-state"),
    path("sync/", CurrentAccessSyncView.as_view(), name="current-access-sync"),
]
