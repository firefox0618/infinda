export type CabinetTab = "overview" | "subscription" | "devices" | "support";

export type CabinetOverviewStat = {
  title: string;
  value: string;
  note: string;
};

export type CabinetAccessState = {
  status:
    | "active"
    | "expired"
    | "pending_payment"
    | "device_limit_exceeded"
    | "restricted"
    | "server_unavailable";
  reason: string;
  subscriptionStatus: string;
  activeDeviceCount: number;
  allowedDeviceCount: number;
  availableRouteCount: number;
  unavailableRouteCodes: readonly string[];
};

export type CabinetDevice = {
  id: number;
  displayName: string;
  icon: "desktop" | "mobile" | "laptop";
  ip: string;
  lastSeen: string;
  computedStatus: "active" | "revoked" | "stale" | "limit_exceeded";
  isCurrent: boolean;
  revokedAt: string | null;
  revokedReason: string;
  meta: string;
  platform: string;
  client: string;
};

export type CabinetProfile = {
  id: number;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  telegramHandle: string;
};

export type CabinetSubscriptionRoute = {
  code: string;
  label: string;
  url: string;
};

export type CabinetSubscriptionStatus =
  | "none"
  | "trial"
  | "active"
  | "expired"
  | "pending_payment";

export type CabinetPaymentHistoryEntry = {
  id: number;
  planCode: string;
  planName: string;
  amountRub: number;
  status: string;
  createdAt: string;
  paidAt: string | null;
};

export type CabinetSubscriptionHistoryEntry = {
  id: number;
  eventType: "trial_started" | "activated" | "renewed";
  planCode: string;
  planName: string;
  startsAt: string;
  endsAt: string;
  createdAt: string;
};

export type CabinetSubscription = {
  status: CabinetSubscriptionStatus;
  isTrial: boolean;
  planName: string | null;
  mainLink: string | null;
  activeUntil: string | null;
  remainingDays: number;
  maxDevices: number | null;
  countries: readonly CabinetSubscriptionRoute[];
  paymentHistory: readonly CabinetPaymentHistoryEntry[];
  subscriptionHistory: readonly CabinetSubscriptionHistoryEntry[];
  pendingPayment: CabinetPaymentHistoryEntry | null;
};

export type CabinetMessageAttachment = {
  id: number;
  name: string;
  url: string;
};

export type CabinetMessage = {
  id: string;
  author: string;
  side: "support" | "user";
  text: string;
  createdAt: string;
  attachments?: readonly CabinetMessageAttachment[];
};

export type CabinetSupportConversationStatus = "new" | "in_progress" | "closed";

export type CabinetSupportConversation = {
  id: number;
  status: CabinetSupportConversationStatus;
  assignedAdminName: string | null;
  lastMessageAt: string | null;
  messages: readonly CabinetMessage[];
};

export type CabinetTelegramLink = {
  isLinked: boolean;
  telegramUserId: number | null;
  telegramUsername: string | null;
  telegramFullName: string | null;
  linkedAt: string | null;
  pendingLinkExpiresAt: string | null;
  pendingDeepLinkUrl: string | null;
};
