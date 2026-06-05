import type {
  CabinetDevice,
  CabinetProfile,
  CabinetSubscription,
} from "../components/cabinet-models";
import {
  devicesApiPaths,
  type FilledSubscriptionDto,
  type SubscriptionCheckoutRequestDto,
  type SubscriptionCheckoutDto,
  profileApiPaths,
  subscriptionApiPaths,
  type DeviceDto,
  type ProfileDto,
  type SubscriptionPlanDto,
  type SubscriptionDto,
  type UpdateProfileRequestDto,
} from "@infinda/shared/contracts";
import {
  extractApiError,
  parseJsonResponse,
  type ApiErrorPayload,
} from "@/shared/api/api-errors";

export type CabinetSubscriptionPlan = {
  code: string;
  title: string;
  durationDays: number;
  priceRub: number;
  maxDevices: number;
  description: string;
};

export type CabinetSubscriptionCheckout = {
  paymentId: number;
  checkoutUrl: string;
  status: string;
  provider: string;
  paymentMethod: string;
  planCode: string;
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

function mapDevice(device: DeviceDto): CabinetDevice {
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

function mapProfile(profile: ProfileDto): CabinetProfile {
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

function mapSubscription(subscription: SubscriptionDto): CabinetSubscription {
  if (subscription.status === "none") {
    return {
      status: "none",
      isTrial: false,
      planName: null,
      mainLink: null,
      activeUntil: null,
      remainingDays: 0,
      maxDevices: null,
      countries: [],
    };
  }

  const resolvedSubscription = subscription as FilledSubscriptionDto;

  return {
    status: resolvedSubscription.status,
    isTrial: resolvedSubscription.is_trial,
    planName: resolvedSubscription.plan_name,
    mainLink: resolvedSubscription.main_link,
    activeUntil: mapDate(resolvedSubscription.active_until),
    remainingDays: resolvedSubscription.remaining_days,
    maxDevices: resolvedSubscription.max_devices,
    countries: resolvedSubscription.countries,
  };
}

async function parseError(response: Response, fallbackMessage: string) {
  const payload = parseJsonResponse<ApiErrorPayload>(await response.text());
  const error = extractApiError(payload);
  return error?.message ?? fallbackMessage;
}

function mapSubscriptionPlan(plan: SubscriptionPlanDto): CabinetSubscriptionPlan {
  return {
    code: plan.code,
    title: plan.title,
    durationDays: plan.duration_days,
    priceRub: plan.price_rub,
    maxDevices: plan.max_devices,
    description: plan.description,
  };
}

export async function fetchCabinetProfile(token: string) {
  const response = await fetch(`/api/${profileApiPaths.me}`, {
    headers: {
      Authorization: `Token ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(await parseError(response, "Не удалось получить профиль."));
  }

  const payload = parseJsonResponse<ProfileDto>(await response.text()) as ProfileDto;
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
  const requestPayload: UpdateProfileRequestDto = {
    email: payload.email,
    first_name: payload.firstName,
    last_name: payload.lastName,
    telegram_handle: payload.telegramHandle,
    current_password: payload.currentPassword,
    new_password: payload.newPassword,
  };

  const response = await fetch(`/api/${profileApiPaths.me}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Token ${token}`,
    },
    body: JSON.stringify(requestPayload),
  });

  if (!response.ok) {
    throw new Error(await parseError(response, "Не удалось обновить профиль."));
  }

  const responsePayload = parseJsonResponse<ProfileDto>(
    await response.text(),
  ) as ProfileDto;
  return mapProfile(responsePayload);
}

export async function fetchCabinetDevices(token: string) {
  const response = await fetch(`/api/${devicesApiPaths.list}`, {
    headers: {
      Authorization: `Token ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(
      await parseError(response, "Не удалось получить список устройств."),
    );
  }

  const payload = parseJsonResponse<DeviceDto[]>(await response.text()) as DeviceDto[];
  return payload.map(mapDevice);
}

export async function fetchCabinetSubscription(token: string) {
  const response = await fetch(`/api/${subscriptionApiPaths.current}`, {
    headers: {
      Authorization: `Token ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(
      await parseError(response, "Не удалось получить данные подписки."),
    );
  }

  const payload = parseJsonResponse<SubscriptionDto>(
    await response.text(),
  ) as SubscriptionDto;
  return mapSubscription(payload);
}

export async function fetchCabinetSubscriptionPlans(token: string) {
  const response = await fetch(`/api/${subscriptionApiPaths.plans}`, {
    headers: {
      Authorization: `Token ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(
      await parseError(response, "Не удалось получить список тарифов."),
    );
  }

  const payload = parseJsonResponse<SubscriptionPlanDto[]>(
    await response.text(),
  ) as SubscriptionPlanDto[];
  return payload.map(mapSubscriptionPlan);
}

export async function createCabinetSubscriptionCheckout(
  token: string,
  planCode: string,
) {
  const requestPayload: SubscriptionCheckoutRequestDto = {
    plan_code: planCode,
  };

  const response = await fetch(`/api/${subscriptionApiPaths.checkout}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Token ${token}`,
    },
    body: JSON.stringify(requestPayload),
  });

  if (!response.ok) {
    throw new Error(
      await parseError(response, "Не удалось создать платеж."),
    );
  }

  const payload = parseJsonResponse<SubscriptionCheckoutDto>(
    await response.text(),
  ) as SubscriptionCheckoutDto;
  return {
    paymentId: payload.payment_id,
    checkoutUrl: payload.checkout_url,
    status: payload.status,
    provider: payload.provider,
    paymentMethod: payload.payment_method,
    planCode: payload.plan_code,
  } satisfies CabinetSubscriptionCheckout;
}

export async function revokeCabinetDevice(token: string, deviceId: number) {
  const response = await fetch(`/api/${devicesApiPaths.revoke(deviceId)}`, {
    method: "POST",
    headers: {
      Authorization: `Token ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(await parseError(response, "Не удалось отозвать устройство."));
  }
}
