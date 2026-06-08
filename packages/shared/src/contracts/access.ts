export const accessApiPaths = {
  current: "access/",
  sync: "access/sync/",
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
  provisioning_issue_count: number;
  last_provisioning_error_codes: string[];
  active_provisioned_binding_count: number;
  error_provisioned_binding_count: number;
  unhealthy_provisioning_server_count: number;
  degraded_provisioning_server_count: number;
};

export type AccessSyncDto = {
  scheduled_operation_count: number;
  failed_operation_count: number;
};
