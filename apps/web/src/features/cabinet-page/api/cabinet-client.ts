import type {
  CabinetDevice,
  CabinetProfile,
  CabinetSubscription,
} from "../components/cabinet-models";

type ApiDevice = {
  id: number;
  name: string;
  icon: "desktop" | "mobile" | "laptop";
  ip: string;
  last_seen: string;
  status: "online" | "offline";
  platform_name: string;
  client_name: string;
  meta: string;
};

type ApiProfile = {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  telegram_handle: string;
};

type ApiSubscriptionRoute = {
  code: string;
  label: string;
  url: string;
};

type ApiSubscription = {
  plan_name: string;
  main_link: string;
  active_until: string;
  remaining_days: number;
  max_devices: number;
  countries: ApiSubscriptionRoute[];
};

function formatLastSeen(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function mapDevice(device: ApiDevice): CabinetDevice {
  return {
    id: device.id,
    name: device.name,
    icon: device.icon,
    ip: device.ip,
    lastSeen: formatLastSeen(device.last_seen),
    status: device.status,
    meta: device.meta,
    platformName: device.platform_name,
    clientName: device.client_name,
  };
}

function mapProfile(profile: ApiProfile): CabinetProfile {
  return {
    id: profile.id,
    username: profile.username,
    email: profile.email,
    firstName: profile.first_name,
    lastName: profile.last_name,
    telegramHandle: profile.telegram_handle,
  };
}

function mapDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  }).format(date);
}

function mapSubscription(subscription: ApiSubscription): CabinetSubscription {
  return {
    planName: subscription.plan_name,
    mainLink: subscription.main_link,
    activeUntil: mapDate(subscription.active_until),
    remainingDays: subscription.remaining_days,
    maxDevices: subscription.max_devices,
    countries: subscription.countries,
  };
}

export async function fetchCabinetProfile(token: string) {
  const response = await fetch("/api/profile/me/", {
    headers: {
      Authorization: `Token ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Не удалось получить профиль.");
  }

  const payload = (await response.json()) as ApiProfile;
  return mapProfile(payload);
}

export async function updateCabinetProfile(
  token: string,
  payload: {
    email: string;
    firstName: string;
    lastName: string;
    telegramHandle: string;
    currentPassword?: string;
    newPassword?: string;
  },
) {
  const response = await fetch("/api/profile/me/", {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Token ${token}`,
    },
    body: JSON.stringify({
      email: payload.email,
      first_name: payload.firstName,
      last_name: payload.lastName,
      telegram_handle: payload.telegramHandle,
      current_password: payload.currentPassword,
      new_password: payload.newPassword,
    }),
  });

  if (!response.ok) {
    throw new Error("Не удалось обновить профиль.");
  }

  const responsePayload = (await response.json()) as ApiProfile;
  return mapProfile(responsePayload);
}

export async function fetchCabinetDevices(token: string) {
  const response = await fetch("/api/devices/", {
    headers: {
      Authorization: `Token ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Не удалось получить список устройств.");
  }

  const payload = (await response.json()) as ApiDevice[];
  return payload.map(mapDevice);
}

export async function fetchCabinetSubscription(token: string) {
  const response = await fetch("/api/subscription/", {
    headers: {
      Authorization: `Token ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Не удалось получить данные подписки.");
  }

  const payload = (await response.json()) as ApiSubscription;
  return mapSubscription(payload);
}

export async function revokeCabinetDevice(token: string, deviceId: number) {
  const response = await fetch(`/api/devices/${deviceId}/revoke/`, {
    method: "POST",
    headers: {
      Authorization: `Token ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Не удалось отозвать устройство.");
  }
}
