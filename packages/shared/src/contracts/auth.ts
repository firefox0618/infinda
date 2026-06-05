export const authApiPaths = {
  login: "auth/login/",
  register: "auth/register/",
  logout: "auth/logout/",
  me: "auth/me/",
} as const;

export type AuthUserDto = {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
};

export type LoginRequestDto = {
  email: string;
  password: string;
};

export type RegisterRequestDto = {
  name?: string;
  email: string;
  password: string;
};

export type AuthSessionDto = {
  token: string;
  user: AuthUserDto;
};

export type RegisterResponseDto = {
  message: string;
  user: AuthUserDto;
};
