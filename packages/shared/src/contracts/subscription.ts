export const subscriptionApiPaths = {
  current: "subscription/",
  plans: "subscription/plans/",
  checkout: "subscription/checkout/",
  adminPayments: "subscription/admin/payments/",
  adminPaymentStatus: (paymentId: number) => `subscription/admin/payments/${paymentId}/status/`,
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
  is_provisioned: boolean;
  client_links: SubscriptionClientLinkDto[];
};

export type SubscriptionClientLinkDto = {
  code: string;
  label: string;
  kind: "happ" | "generic" | "routing";
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
  feed_link: string;
  happ_link: string;
  happ_deep_link: string;
  happ_routing_link: string;
  client_links: SubscriptionClientLinkDto[];
  active_until: string;
  remaining_days: number;
  max_devices: number;
  uses_provisioned_access: boolean;
  provisioned_route_count: number;
  resolved_device_name: string | null;
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

export type OperatorSubscriptionPaymentDto = {
  id: number;
  user_email: string;
  plan_code: string;
  plan_name: string;
  amount_rub: number;
  status: string;
  provider: string;
  payment_method: string;
  provider_status: string;
  external_payment_id: string | null;
  checkout_url: string;
  created_at: string;
  paid_at: string | null;
};

export type OperatorSubscriptionPaymentStatusRequestDto = {
  status: "paid" | "canceled" | "failed";
};
