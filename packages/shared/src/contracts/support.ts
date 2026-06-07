export const supportApiPaths = {
  conversation: "support/conversation/",
  messages: "support/messages/",
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

