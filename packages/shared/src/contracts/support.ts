export const supportApiPaths = {
  conversation: "support/conversation/",
  messages: "support/messages/",
  adminConversations: "support/admin/conversations/",
  adminAssignConversation: (conversationId: number) =>
    `support/admin/conversations/${conversationId}/assign/`,
  adminReplyConversation: (conversationId: number) =>
    `support/admin/conversations/${conversationId}/reply/`,
  adminCloseConversation: (conversationId: number) =>
    `support/admin/conversations/${conversationId}/close/`,
} as const;

export type SupportConversationStatusDto = "new" | "in_progress" | "closed";
export type SupportMessageSenderTypeDto = "user" | "admin";
export type SupportMessageSourceDto = "web" | "telegram_support_bot" | "admin";

export type SupportAttachmentDto = {
  id: number;
  file_name: string;
  content_type: string;
  size_bytes: number;
  url: string;
};

export type SupportMessageDto = {
  id: number;
  sender_type: SupportMessageSenderTypeDto;
  sender_display_name: string;
  source: SupportMessageSourceDto;
  text: string;
  created_at: string;
  attachments: SupportAttachmentDto[];
};

export type SupportConversationDto = {
  id: number;
  status: SupportConversationStatusDto;
  assigned_admin_name: string | null;
  last_message_at: string | null;
  created_at: string;
  updated_at: string;
  closed_at: string | null;
  messages: SupportMessageDto[];
};

export type OperatorSupportConversationDto = SupportConversationDto & {
  user_id: number;
  user_email: string;
  user_display_name: string;
  delivery_channel: "web" | "telegram_support_bot";
  assigned_admin_id: number | null;
  last_message_preview: string;
};

export type OperatorSupportAssignRequestDto = {
  admin_user_id?: number;
};

export type OperatorSupportReplyRequestDto = {
  text?: string;
  close_after_reply?: boolean;
};
