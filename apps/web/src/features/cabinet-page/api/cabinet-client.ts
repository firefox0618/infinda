import type {
  CabinetAccessState,
  CabinetDevice,
  CabinetPaymentHistoryEntry,
  CabinetProfile,
  CabinetSubscriptionHistoryEntry,
  CabinetSupportConversation,
  CabinetTelegramLink,
  CabinetSubscription,
} from "../components/cabinet-models";
import {
  accessApiPaths,
  type AccessStateDto,
  devicesApiPaths,
  type DeviceDto,
  type FilledSubscriptionDto,
  profileApiPaths,
  type RevokeDeviceRequestDto,
  type ProfileDto,
  subscriptionApiPaths,
  supportApiPaths,
  type SubscriptionCheckoutDto,
  type SubscriptionCheckoutRequestDto,
  type SubscriptionDto,
  type SubscriptionHistoryEventDto,
  type SubscriptionPaymentHistoryDto,
  type SubscriptionPlanDto,
  type SupportConversationDto,
  telegramApiPaths,
  type TelegramLinkStatusDto,
  type TelegramLinkTokenDto,
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

export class CabinetRequestError extends Error {
  errorCode?: string;

  constructor(message: string, errorCode?: string) {
    super(message);
    this.name = "CabinetRequestError";
    this.errorCode = errorCode;
  }
}

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
    displayName: device.display_name,
    icon: device.icon,
    ip: device.ip,
    lastSeen: formatLastSeen(device.last_seen),
    computedStatus: device.computed_status,
    isCurrent: device.is_current,
    revokedAt: mapDateTime(device.revoked_at),
    revokedReason: device.revoked_reason,
    meta: device.meta,
    platform: device.platform,
    client: device.client,
  };
}

function mapAccessState(accessState: AccessStateDto): CabinetAccessState {
  return {
    status: accessState.status,
    reason: accessState.reason,
    subscriptionStatus: accessState.subscription_status,
    activeDeviceCount: accessState.active_device_count,
    allowedDeviceCount: accessState.allowed_device_count,
    availableRouteCount: accessState.available_route_count,
    unavailableRouteCodes: accessState.unavailable_route_codes,
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

function mapDateTime(value: string | null) {
  if (!value) {
    return null;
  }

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

function mapPaymentHistoryEntry(
  entry: SubscriptionPaymentHistoryDto,
): CabinetPaymentHistoryEntry {
  return {
    id: entry.id,
    planCode: entry.plan_code,
    planName: entry.plan_name,
    amountRub: entry.amount_rub,
    status: entry.status,
    createdAt: mapDateTime(entry.created_at) ?? entry.created_at,
    paidAt: mapDateTime(entry.paid_at),
  };
}

function mapSubscriptionHistoryEntry(
  entry: SubscriptionHistoryEventDto,
): CabinetSubscriptionHistoryEntry {
  return {
    id: entry.id,
    eventType: entry.event_type,
    planCode: entry.plan_code,
    planName: entry.plan_name,
    startsAt: mapDate(entry.starts_at),
    endsAt: mapDate(entry.ends_at),
    createdAt: mapDateTime(entry.created_at) ?? entry.created_at,
  };
}

function mapSubscription(subscription: SubscriptionDto): CabinetSubscription {
  if (subscription.status === "none" || subscription.status === "pending_payment") {
    return {
      status: subscription.status,
      isTrial: false,
      planName: null,
      mainLink: null,
      activeUntil: null,
      remainingDays: 0,
      maxDevices: null,
      countries: [],
      paymentHistory: [],
      subscriptionHistory: [],
      pendingPayment: subscription.pending_payment
        ? mapPaymentHistoryEntry(subscription.pending_payment)
        : null,
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
    paymentHistory: resolvedSubscription.payment_history.map(mapPaymentHistoryEntry),
    subscriptionHistory: resolvedSubscription.subscription_history.map(
      mapSubscriptionHistoryEntry,
    ),
    pendingPayment: resolvedSubscription.pending_payment
      ? mapPaymentHistoryEntry(resolvedSubscription.pending_payment)
      : null,
  };
}

function mapSupportConversation(
  conversation: SupportConversationDto,
): CabinetSupportConversation {
  return {
    id: conversation.id,
    status: conversation.status,
    assignedAdminName: conversation.assigned_admin_name,
    lastMessageAt: mapDateTime(conversation.last_message_at),
    messages: conversation.messages.map((message) => ({
      id: String(message.id),
      author: message.sender_display_name,
      side: message.sender_type === "user" ? "user" : "support",
      text: message.text,
      createdAt: mapDateTime(message.created_at) ?? message.created_at,
      attachments: message.attachments.map((attachment) => ({
        id: attachment.id,
        name: attachment.file_name,
        url: attachment.url,
      })),
    })),
  };
}

function mapTelegramLinkStatus(status: TelegramLinkStatusDto): CabinetTelegramLink {
  return {
    isLinked: status.is_linked,
    telegramUserId: status.telegram_user_id,
    telegramUsername: status.telegram_username,
    telegramFullName: status.telegram_full_name,
    linkedAt: mapDateTime(status.linked_at),
    pendingLinkExpiresAt: mapDateTime(status.pending_link_expires_at),
    pendingDeepLinkUrl: status.pending_deep_link_url,
  };
}

async function parseError(response: Response, fallbackMessage: string) {
  const payload = parseJsonResponse<ApiErrorPayload>(await response.text());
  const error = extractApiError(payload);
  return {
    message: error?.message ?? fallbackMessage,
    errorCode: error?.code,
  };
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
    const error = await parseError(response, "Не удалось получить профиль.");
    throw new CabinetRequestError(error.message, error.errorCode);
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
    const error = await parseError(response, "Не удалось обновить профиль.");
    throw new CabinetRequestError(error.message, error.errorCode);
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
    const error = await parseError(response, "Не удалось получить список устройств.");
    throw new CabinetRequestError(error.message, error.errorCode);
  }

  const payload = parseJsonResponse<DeviceDto[]>(await response.text()) as DeviceDto[];
  return payload.map(mapDevice);
}

export async function fetchCabinetAccessState(token: string) {
  const response = await fetch(`/api/${accessApiPaths.current}`, {
    headers: {
      Authorization: `Token ${token}`,
    },
  });

  if (!response.ok) {
    const error = await parseError(response, "Не удалось получить состояние доступа.");
    throw new CabinetRequestError(error.message, error.errorCode);
  }

  const payload = parseJsonResponse<AccessStateDto>(await response.text()) as AccessStateDto;
  return mapAccessState(payload);
}

export async function fetchCabinetSubscription(token: string) {
  const response = await fetch(`/api/${subscriptionApiPaths.current}`, {
    headers: {
      Authorization: `Token ${token}`,
    },
  });

  if (!response.ok) {
    const error = await parseError(response, "Не удалось получить данные подписки.");
    throw new CabinetRequestError(error.message, error.errorCode);
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
    const error = await parseError(response, "Не удалось получить список тарифов.");
    throw new CabinetRequestError(error.message, error.errorCode);
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
    const error = await parseError(response, "Не удалось создать платеж.");
    throw new CabinetRequestError(error.message, error.errorCode);
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

export async function revokeCabinetDevice(
  token: string,
  deviceId: number,
  reason?: string,
) {
  const requestPayload: RevokeDeviceRequestDto | undefined =
    reason && reason.trim() ? { reason: reason.trim() } : undefined;
  const response = await fetch(`/api/${devicesApiPaths.revoke(deviceId)}`, {
    method: "POST",
    headers: {
      ...(requestPayload ? { "Content-Type": "application/json" } : {}),
      Authorization: `Token ${token}`,
    },
    body: requestPayload ? JSON.stringify(requestPayload) : undefined,
  });

  if (!response.ok) {
    const error = await parseError(response, "Не удалось отозвать устройство.");
    throw new CabinetRequestError(error.message, error.errorCode);
  }

  const payload = parseJsonResponse<DeviceDto>(await response.text()) as DeviceDto;
  return mapDevice(payload);
}

export async function fetchCabinetSupportConversation(token: string) {
  const response = await fetch(`/api/${supportApiPaths.conversation}`, {
    headers: {
      Authorization: `Token ${token}`,
    },
  });

  if (!response.ok) {
    const error = await parseError(response, "Не удалось загрузить диалог поддержки.");
    throw new CabinetRequestError(error.message, error.errorCode);
  }

  const payload = parseJsonResponse<SupportConversationDto>(
    await response.text(),
  ) as SupportConversationDto;
  return mapSupportConversation(payload);
}

export async function sendCabinetSupportMessage(
  token: string,
  payload: {
    text: string;
    files: File[];
  },
) {
  const formData = new FormData();
  formData.set("text", payload.text);

  payload.files.forEach((file) => {
    formData.append("attachments", file);
  });

  const response = await fetch(`/api/${supportApiPaths.messages}`, {
    method: "POST",
    headers: {
      Authorization: `Token ${token}`,
    },
    body: formData,
  });

  if (!response.ok) {
    const error = await parseError(response, "Не удалось отправить сообщение в поддержку.");
    throw new CabinetRequestError(error.message, error.errorCode);
  }

  const responsePayload = parseJsonResponse<SupportConversationDto>(
    await response.text(),
  ) as SupportConversationDto;
  return mapSupportConversation(responsePayload);
}

export async function fetchCabinetTelegramLinkStatus(token: string) {
  const response = await fetch(`/api/${telegramApiPaths.link}`, {
    headers: {
      Authorization: `Token ${token}`,
    },
  });

  if (!response.ok) {
    const error = await parseError(response, "Не удалось получить статус Telegram.");
    throw new CabinetRequestError(error.message, error.errorCode);
  }

  const payload = parseJsonResponse<TelegramLinkStatusDto>(
    await response.text(),
  ) as TelegramLinkStatusDto;
  return mapTelegramLinkStatus(payload);
}

export async function createCabinetTelegramLinkToken(token: string) {
  const response = await fetch(`/api/${telegramApiPaths.link}`, {
    method: "POST",
    headers: {
      Authorization: `Token ${token}`,
    },
  });

  if (!response.ok) {
    const error = await parseError(response, "Не удалось создать ссылку привязки Telegram.");
    throw new CabinetRequestError(error.message, error.errorCode);
  }

  const payload = parseJsonResponse<TelegramLinkTokenDto>(
    await response.text(),
  ) as TelegramLinkTokenDto;
  return {
    token: payload.token,
    deepLinkUrl: payload.deep_link_url,
    expiresAt: mapDateTime(payload.expires_at) ?? payload.expires_at,
  };
}

export async function unlinkCabinetTelegram(token: string) {
  const response = await fetch(`/api/${telegramApiPaths.link}`, {
    method: "DELETE",
    headers: {
      Authorization: `Token ${token}`,
    },
  });

  if (!response.ok) {
    const error = await parseError(response, "Не удалось отвязать Telegram.");
    throw new CabinetRequestError(error.message, error.errorCode);
  }

  const payload = parseJsonResponse<TelegramLinkStatusDto>(
    await response.text(),
  ) as TelegramLinkStatusDto;
  return mapTelegramLinkStatus(payload);
}
