const DEVICE_KEY_STORAGE_PREFIX = "public-subscription-device-key:";

function buildStorageKey(token: string) {
  return `${DEVICE_KEY_STORAGE_PREFIX}${token}`;
}

function buildRandomKey() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID().replace(/-/g, "");
  }
  return `${Date.now().toString(36)}${Math.random().toString(36).slice(2)}`;
}

export function getStoredPublicDeviceKey(token: string) {
  if (typeof window === "undefined") {
    return null;
  }
  const value = window.localStorage.getItem(buildStorageKey(token));
  return value && value.trim() ? value.trim() : null;
}

export function ensurePublicDeviceKey(token: string) {
  const existing = getStoredPublicDeviceKey(token);
  if (existing) {
    return existing;
  }
  const created = buildRandomKey();
  window.localStorage.setItem(buildStorageKey(token), created);
  return created;
}
