import { authApiPaths } from "@infinda/shared/contracts/auth";
import { apiErrorCodes } from "@infinda/shared/contracts/errors";
import {
  extractApiError,
  parseJsonResponse,
  type ApiErrorPayload,
} from "@/shared/api/api-errors";
import type {
  AuthFieldErrors,
  AuthSession,
  AuthUser,
  LoginPayload,
  RegisterPayload,
  RegisterResponse,
} from "./auth-types";

export class AuthRequestError extends Error {
  fieldErrors?: AuthFieldErrors;
  errorCode?: string;

  constructor(message: string, fieldErrors?: AuthFieldErrors, errorCode?: string) {
    super(message);
    this.name = "AuthRequestError";
    this.fieldErrors = fieldErrors;
    this.errorCode = errorCode;
  }
}

function getErrorMessage(value: string[] | string | undefined) {
  if (Array.isArray(value)) {
    return value[0];
  }

  return value;
}

function buildFieldErrors(payload: ApiErrorPayload) {
  const error = extractApiError(payload);

  if (!error) {
    return undefined;
  }

  const details = error.details as {
    name?: string[] | string;
    email?: string[] | string;
    password?: string[] | string;
  };

  const fieldErrors: AuthFieldErrors = {
    name: getErrorMessage(details.name),
    email: getErrorMessage(details.email),
    password: getErrorMessage(details.password),
  };

  if (!fieldErrors.name && !fieldErrors.email && !fieldErrors.password) {
    return undefined;
  }

  return fieldErrors;
}

export async function loginWithPassword(payload: LoginPayload) {
  const response = await fetch(`/api/${authApiPaths.login}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const responsePayload = parseJsonResponse<AuthSession | ApiErrorPayload>(
    await response.text(),
  );

  if (!response.ok) {
    const fieldErrors = buildFieldErrors(responsePayload as ApiErrorPayload);
    const apiError = extractApiError(responsePayload as ApiErrorPayload);
    const message =
      apiError?.message ??
      fieldErrors?.email ??
      fieldErrors?.password ??
      (apiError?.code === apiErrorCodes.authenticationFailed
        ? "Не удалось выполнить вход."
        : "Не удалось выполнить вход.");

    throw new AuthRequestError(message, fieldErrors, apiError?.code);
  }

  return responsePayload as AuthSession;
}

export async function registerWithPassword(payload: RegisterPayload) {
  const response = await fetch(`/api/${authApiPaths.register}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const responsePayload = parseJsonResponse<RegisterResponse | ApiErrorPayload>(
    await response.text(),
  );

  if (!response.ok) {
    const fieldErrors = buildFieldErrors(responsePayload as ApiErrorPayload);
    const apiError = extractApiError(responsePayload as ApiErrorPayload);

    throw new AuthRequestError(
      apiError?.message ??
        fieldErrors?.name ??
        fieldErrors?.email ??
        fieldErrors?.password ??
        "Не удалось зарегистрировать пользователя.",
      fieldErrors,
      apiError?.code,
    );
  }

  return responsePayload as RegisterResponse;
}

export async function fetchCurrentUser(token: string) {
  const response = await fetch(`/api/${authApiPaths.me}`, {
    headers: {
      Authorization: `Token ${token}`,
    },
  });

  const responsePayload = parseJsonResponse<AuthUser | ApiErrorPayload>(
    await response.text(),
  );

  if (!response.ok) {
    const errorPayload = extractApiError(responsePayload as ApiErrorPayload);
    throw new AuthRequestError(
      errorPayload?.message ?? "Не удалось получить данные пользователя.",
      undefined,
      errorPayload?.code,
    );
  }

  return responsePayload as AuthUser;
}

export async function logoutCurrentUser(token: string) {
  const response = await fetch(`/api/${authApiPaths.logout}`, {
    method: "POST",
    headers: {
      Authorization: `Token ${token}`,
    },
  });

  if (!response.ok && response.status !== 204) {
    const errorPayload = extractApiError(
      parseJsonResponse<ApiErrorPayload>(await response.text()),
    );
    throw new AuthRequestError(
      errorPayload?.message ?? "Не удалось завершить сеанс.",
      undefined,
      errorPayload?.code,
    );
  }
}
