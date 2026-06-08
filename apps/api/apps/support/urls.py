from django.urls import path

from .views import (
    AdminSupportConversationAssignView,
    AdminSupportConversationCloseView,
    AdminSupportConversationListView,
    AdminSupportConversationReplyView,
    CurrentSupportConversationView,
    SupportMessageCreateView,
)


urlpatterns = [
    path("conversation/", CurrentSupportConversationView.as_view(), name="support-conversation"),
    path("messages/", SupportMessageCreateView.as_view(), name="support-message-create"),
    path("admin/conversations/", AdminSupportConversationListView.as_view(), name="support-admin-conversation-list"),
    path(
        "admin/conversations/<int:conversation_id>/assign/",
        AdminSupportConversationAssignView.as_view(),
        name="support-admin-conversation-assign",
    ),
    path(
        "admin/conversations/<int:conversation_id>/reply/",
        AdminSupportConversationReplyView.as_view(),
        name="support-admin-conversation-reply",
    ),
    path(
        "admin/conversations/<int:conversation_id>/close/",
        AdminSupportConversationCloseView.as_view(),
        name="support-admin-conversation-close",
    ),
]
