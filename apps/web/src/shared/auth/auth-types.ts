export type AuthUser = {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
};

export type LoginPayload = {
  email: string;
  password: string;
};

export type AuthSession = {
  token: string;
  user: AuthUser;
};

export type AuthFieldErrors = {
  email?: string;
  password?: string;
};
