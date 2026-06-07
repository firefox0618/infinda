export const subscriptionApiPaths = {
  current: "subscription/",
  plans: "subscription/plans/",
  checkout: "subscription/checkout/",
} as const;

export type SubscriptionStatusDto =
  | "none"
  | "trial"
  | "active"
  | "expired"
  | "pending_payment";

export type SubscriptionRouteDto = {
  code: string;
  label: string;
  url: string;
};

export type EmptySubscriptionDto = {
  status: "none" | "pending_payment";
  pending_payment: SubscriptionPaymentHistoryDto | null;
};

export type SubscriptionPaymentHistoryDto = {
  id: number;
  plan_code: string;
  plan_name: string;
  amount_rub: number;
  status: string;
  created_at: string;
  paid_at: string | null;
};

export type SubscriptionHistoryEventDto = {
  id: number;
  event_type: "trial_started" | "activated" | "renewed";
  plan_code: string;
  plan_name: string;
  starts_at: string;
  ends_at: string;
  created_at: string;
};

export type FilledSubscriptionDto = {
  status: Exclude<SubscriptionStatusDto, "none">;
  is_trial: boolean;
  plan_name: string;
  main_link: string;
  active_until: string;
  remaining_days: number;
  max_devices: number;
  countries: SubscriptionRouteDto[];
  payment_history: SubscriptionPaymentHistoryDto[];
  subscription_history: SubscriptionHistoryEventDto[];
  pending_payment: SubscriptionPaymentHistoryDto | null;
};

export type SubscriptionDto = EmptySubscriptionDto | FilledSubscriptionDto;

export type SubscriptionPlanDto = {
  code: string;
  title: string;
  duration_days: number;
  price_rub: number;
  max_devices: number;
  description: string;
};

export type SubscriptionCheckoutRequestDto = {
  plan_code: string;
};

export type SubscriptionCheckoutDto = {
  payment_id: number;
  checkout_url: string;
  status: string;
  provider: string;
  payment_method: string;
  plan_code: string;
};
