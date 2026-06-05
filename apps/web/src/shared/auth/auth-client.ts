import type {
  AuthFieldErrors,
  AuthSession,
  AuthUser,
  LoginPayload,
} from "./auth-types";

type ErrorPayload = {
  detail?: string;
  email?: string[] | string;
  password?: string[] | string;
};

export class AuthRequestError extends Error {
  fieldErrors?: AuthFieldErrors;

  constructor(message: string, fieldErrors?: AuthFieldErrors) {
    super(message);
    this.name = "AuthRequestError";
    this.fieldErrors = fieldErrors;
  }
}

function getErrorMessage(value: string[] | string | undefined) {
  if (Array.isArray(value)) {
    return value[0];
  }

  return value;
}

async function parseJson<T>(response: Response) {
  const text = await response.text();

  if (!text) {
    return null as T | null;
  }

  return JSON.parse(text) as T;
}

function buildFieldErrors(payload: ErrorPayload | null) {
  if (!payload) {
    return undefined;
  }

  const fieldErrors: AuthFieldErrors = {
    email: getErrorMessage(payload.email),
    password: getErrorMessage(payload.password),
  };

  if (!fieldErrors.email && !fieldErrors.password) {
    return undefined;
  }

  return fieldErrors;
}

export async function loginWithPassword(payload: LoginPayload) {
  const response = await fetch("/api/auth/login/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const responsePayload = await parseJson<AuthSession | ErrorPayload>(response);

  if (!response.ok) {
    const errorPayload = responsePayload as ErrorPayload | null;
    const fieldErrors = buildFieldErrors(errorPayload);
    const message =
      errorPayload?.detail ??
      fieldErrors?.email ??
      fieldErrors?.password ??
      "Не удалось выполнить вход.";

    throw new AuthRequestError(message, fieldErrors);
  }

  return responsePayload as AuthSession;
}

export async function fetchCurrentUser(token: string) {
  const response = await fetch("/api/auth/me/", {
    headers: {
      Authorization: `Token ${token}`,
    },
  });

  const responsePayload = await parseJson<AuthUser | ErrorPayload>(response);

  if (!response.ok) {
    const errorPayload = responsePayload as ErrorPayload | null;
    throw new AuthRequestError(
      errorPayload?.detail ?? "Не удалось получить данные пользователя.",
    );
  }

  return responsePayload as AuthUser;
}

export async function logoutCurrentUser(token: string) {
  const response = await fetch("/api/auth/logout/", {
    method: "POST",
    headers: {
      Authorization: `Token ${token}`,
    },
  });

  if (!response.ok && response.status !== 204) {
    const errorPayload = await parseJson<ErrorPayload>(response);
    throw new AuthRequestError(
      errorPayload?.detail ?? "Не удалось завершить сеанс.",
    );
  }
}
