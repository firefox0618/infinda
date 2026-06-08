export const publicSubscriptionApiPaths = {
  summary: (token: string) => `subscription/public/${token}/summary/`,
  feed: (token: string) => `subscription/public/${token}/feed/`,
  touch: (token: string) => `subscription/public/${token}/touch/`,
} as const;

export type PublicSubscriptionActionLinkDto = {
  label: string;
  url: string;
};

export type PublicSubscriptionInstallGuideDto = {
  code: string;
  title: string;
  description: string;
  links: PublicSubscriptionActionLinkDto[];
};

export type PublicSubscriptionSummaryDto = {
  status: "trial" | "active" | "expired" | "pending_payment";
  is_trial: boolean;
  plan_name: string;
  main_link: string;
  feed_link: string;
  happ_link: string;
  happ_deep_link: string;
  happ_routing_link: string;
  client_links: {
    code: string;
    label: string;
    kind: "happ" | "generic" | "routing";
    url: string;
  }[];
  active_until: string;
  remaining_days: number;
  max_devices: number;
  uses_provisioned_access: boolean;
  provisioned_route_count: number;
  resolved_device_name: string | null;
  install_guides: PublicSubscriptionInstallGuideDto[];
  countries: {
    code: string;
    label: string;
    url: string;
    is_provisioned: boolean;
    client_links: {
      code: string;
      label: string;
      kind: "happ" | "generic" | "routing";
      url: string;
    }[];
  }[];
};

export type PublicSubscriptionTouchDto = {
  ok: boolean;
  created: boolean;
  scheduled_operation_count: number;
  failed_operation_count: number;
  device: {
    id: number;
    display_name: string;
    platform: string;
    client: string;
    ip: string;
  };
};

export type PublicSubscriptionTouchRequestDto = {
  device_name?: string;
  platform?: string;
  client?: string;
  icon?: "desktop" | "mobile" | "laptop";
};
