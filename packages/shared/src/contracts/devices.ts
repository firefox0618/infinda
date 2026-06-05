export const devicesApiPaths = {
  list: "devices/",
  revoke: (deviceId: number | string) => `devices/${deviceId}/revoke/`,
} as const;

export type DeviceIconCode = "desktop" | "mobile" | "laptop";
export type DeviceStatusCode = "online" | "offline";

export type DeviceDto = {
  id: number;
  name: string;
  icon: DeviceIconCode;
  ip: string;
  last_seen: string;
  status: DeviceStatusCode;
  platform_name: string;
  client_name: string;
  meta: string;
};
