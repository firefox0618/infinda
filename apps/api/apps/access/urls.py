from django.urls import path

from .views import CurrentAccessStateView


urlpatterns = [
    path("", CurrentAccessStateView.as_view(), name="current-access-state"),
]
