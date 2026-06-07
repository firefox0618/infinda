export const telegramApiPaths = {
  link: "telegram/link/",
  confirm: "telegram/link/confirm/",
} as const;

export type TelegramLinkStatusDto = {
  is_linked: boolean;
  telegram_user_id: number | null;
  telegram_username: string | null;
  telegram_full_name: string | null;
  linked_at: string | null;
  pending_link_expires_at: string | null;
  pending_deep_link_url: string | null;
};

export type TelegramLinkTokenDto = {
  token: string;
  deep_link_url: string;
  expires_at: string;
};

