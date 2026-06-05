export const profileApiPaths = {
  me: "profile/me/",
} as const;

export type ProfileDto = {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  telegram_handle: string;
};

export type UpdateProfileRequestDto = {
  email?: string;
  first_name?: string;
  last_name?: string;
  telegram_handle?: string;
  current_password?: string;
  new_password?: string;
};
