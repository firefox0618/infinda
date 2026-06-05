export type CabinetTab = "overview" | "subscription" | "devices" | "support";

export type CabinetOverviewStat = {
  title: string;
  value: string;
  note: string;
};

export type CabinetDevice = {
  id: number;
  name: string;
  icon: "desktop" | "mobile" | "laptop";
  ip: string;
  lastSeen: string;
  status: "online" | "offline";
  meta: string;
  platformName: string;
  clientName: string;
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

export type CabinetSubscriptionStatus = "none" | "trial" | "active" | "expired";

export type CabinetSubscription = {
  status: CabinetSubscriptionStatus;
  isTrial: boolean;
  planName: string | null;
  mainLink: string | null;
  activeUntil: string | null;
  remainingDays: number;
  maxDevices: number | null;
  countries: readonly CabinetSubscriptionRoute[];
};

export type CabinetMessage = {
  id: string;
  author: string;
  side: "support" | "user";
  text: string;
  attachments?: readonly string[];
};
