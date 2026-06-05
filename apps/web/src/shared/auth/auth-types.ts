import type {
  AuthSessionDto,
  AuthUserDto,
  LoginRequestDto,
  RegisterRequestDto,
  RegisterResponseDto,
} from "@infinda/shared/contracts/auth";

export type AuthUser = AuthUserDto;
export type LoginPayload = LoginRequestDto;
export type AuthSession = AuthSessionDto;
export type RegisterPayload = RegisterRequestDto;
export type RegisterResponse = RegisterResponseDto;

export type AuthFieldErrors = {
  name?: string;
  email?: string;
  password?: string;
};
