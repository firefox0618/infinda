from django.urls import path

from .views import TelegramLinkConfirmView, TelegramLinkStatusView


urlpatterns = [
    path("link/", TelegramLinkStatusView.as_view(), name="telegram-link"),
    path("link/confirm/", TelegramLinkConfirmView.as_view(), name="telegram-link-confirm"),
]

