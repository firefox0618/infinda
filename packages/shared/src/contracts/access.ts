export const accessApiPaths = {
  current: "access/",
} as const;

export type AccessStateStatusDto =
  | "active"
  | "expired"
  | "pending_payment"
  | "device_limit_exceeded"
  | "restricted"
  | "server_unavailable";

export type AccessStateDto = {
  status: AccessStateStatusDto;
  reason: string;
  subscription_status: string;
  active_device_count: number;
  allowed_device_count: number;
  available_route_count: number;
  unavailable_route_codes: string[];
};
