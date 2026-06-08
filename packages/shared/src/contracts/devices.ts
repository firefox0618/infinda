export const devicesApiPaths = {
  list: "devices/",
  repair: (deviceId: number | string) => `devices/${deviceId}/repair/`,
  revoke: (deviceId: number | string) => `devices/${deviceId}/revoke/`,
} as const;

export type DeviceIconCode = "desktop" | "mobile" | "laptop";
export type DeviceComputedStatusCode =
  | "active"
  | "revoked"
  | "stale"
  | "limit_exceeded";

export type DeviceDto = {
  id: number;
  display_name: string;
  icon: DeviceIconCode;
  ip: string;
  last_seen: string;
  computed_status: DeviceComputedStatusCode;
  is_current: boolean;
  revoked_at: string | null;
  revoked_reason: string;
  platform: string;
  client: string;
  meta: string;
};

export type RevokeDeviceRequestDto = {
  reason?: string;
};

export type RepairDeviceRequestDto = {
  reason?: string;
};

export type RepairDeviceResponseDto = {
  device: DeviceDto;
  scheduled_operation_count: number;
  failed_operation_count: number;
};
