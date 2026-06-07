from django.urls import path

from .views import CurrentSupportConversationView, SupportMessageCreateView


urlpatterns = [
    path("conversation/", CurrentSupportConversationView.as_view(), name="support-conversation"),
    path("messages/", SupportMessageCreateView.as_view(), name="support-message-create"),
]

