export const subscriptionApiPaths = {
  current: "subscription/",
  plans: "subscription/plans/",
  checkout: "subscription/checkout/",
  purchase: "subscription/purchase/",
} as const;

export type SubscriptionStatusDto = "none" | "trial" | "active" | "expired";

export type SubscriptionRouteDto = {
  code: string;
  label: string;
  url: string;
};

export type EmptySubscriptionDto = {
  status: "none";
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

export type PurchaseSubscriptionRequestDto = {
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
