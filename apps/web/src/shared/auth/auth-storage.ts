import type { AuthSession, AuthUser } from "./auth-types";

const AUTH_TOKEN_STORAGE_KEY = "infinda.auth.token";
const AUTH_USER_STORAGE_KEY = "infinda.auth.user";
const AUTH_STORAGE_EVENT = "infinda:auth-storage-change";

type AuthPersistence = "local" | "session";

function isBrowser() {
  return typeof window !== "undefined";
}

function getStorage(persistence: AuthPersistence) {
  return persistence === "local" ? window.localStorage : window.sessionStorage;
}

function readFromStorage(key: string) {
  if (!isBrowser()) {
    return null;
  }

  return (
    window.localStorage.getItem(key) ?? window.sessionStorage.getItem(key)
  );
}

function emitAuthStorageChange() {
  if (!isBrowser()) {
    return;
  }

  window.dispatchEvent(new Event(AUTH_STORAGE_EVENT));
}

export function persistAuthSession(
  session: AuthSession,
  options: { rememberMe: boolean },
) {
  if (!isBrowser()) {
    return;
  }

  clearAuthSession();

  const storage = getStorage(options.rememberMe ? "local" : "session");
  storage.setItem(AUTH_TOKEN_STORAGE_KEY, session.token);
  storage.setItem(AUTH_USER_STORAGE_KEY, JSON.stringify(session.user));
  emitAuthStorageChange();
}

export function readAuthToken() {
  return readFromStorage(AUTH_TOKEN_STORAGE_KEY);
}

export function readStoredAuthUser() {
  const serializedUser = readFromStorage(AUTH_USER_STORAGE_KEY);

  if (!serializedUser) {
    return null;
  }

  try {
    return JSON.parse(serializedUser) as AuthUser;
  } catch {
    return null;
  }
}

export function replaceStoredAuthUser(user: AuthUser) {
  if (!isBrowser()) {
    return;
  }

  const targetStorage = window.localStorage.getItem(AUTH_USER_STORAGE_KEY)
    ? window.localStorage
    : window.sessionStorage.getItem(AUTH_USER_STORAGE_KEY)
      ? window.sessionStorage
      : null;

  if (!targetStorage) {
    return;
  }

  targetStorage.setItem(AUTH_USER_STORAGE_KEY, JSON.stringify(user));
  emitAuthStorageChange();
}

export function subscribeToAuthStorage(onStoreChange: () => void) {
  if (!isBrowser()) {
    return () => undefined;
  }

  const handleStorageChange = () => {
    onStoreChange();
  };

  window.addEventListener("storage", handleStorageChange);
  window.addEventListener(AUTH_STORAGE_EVENT, handleStorageChange);

  return () => {
    window.removeEventListener("storage", handleStorageChange);
    window.removeEventListener(AUTH_STORAGE_EVENT, handleStorageChange);
  };
}

export function readHasAuthSession() {
  return Boolean(readAuthToken());
}

export function clearAuthSession() {
  if (!isBrowser()) {
    return;
  }

  window.localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
  window.localStorage.removeItem(AUTH_USER_STORAGE_KEY);
  window.sessionStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
  window.sessionStorage.removeItem(AUTH_USER_STORAGE_KEY);
  emitAuthStorageChange();
}
