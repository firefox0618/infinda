"use client";

import { useState } from "react";

import styles from "./cabinet-page.module.css";

import { DeviceIcon } from "./cabinet-icons";

type CabinetDevice = {
  name: string;
  icon: "desktop" | "mobile" | "laptop";
  ip: string;
  lastSeen: string;
  status: "online" | "offline";
  meta: string;
};

type CabinetDevicesPanelProps = {
  devices: readonly CabinetDevice[];
  onRevokeDevice: (deviceName: string) => void;
};

export function CabinetDevicesPanel({
  devices,
  onRevokeDevice,
}: CabinetDevicesPanelProps) {
  const [expandedDeviceName, setExpandedDeviceName] = useState<string | null>(
    devices[0]?.name ?? null,
  );

  return (
    <div className={styles.devicesList}>
      {devices.map((device, index) => (
        <article
          key={device.name}
          className={styles.deviceListItem}
          style={{ animationDelay: `${index * 90}ms` }}
        >
          <div className={styles.deviceRow}>
            <button
              type="button"
              className={styles.deviceSummaryButton}
              onClick={() =>
                setExpandedDeviceName((current) =>
                  current === device.name ? null : device.name,
                )
              }
            >
              <div className={styles.deviceIdentity}>
                <span className={styles.devicePlatformIcon} aria-hidden="true">
                  <DeviceIcon kind={device.icon} />
                </span>
                <div>
                  <div className={styles.deviceName}>{device.name}</div>
                  <div className={styles.deviceMeta}>{device.meta}</div>
                </div>
              </div>
              <span
                className={`${styles.deviceStatus} ${
                  device.status === "online"
                    ? styles.deviceStatusOnline
                    : styles.deviceStatusOffline
                }`}
              >
                {device.status === "online" ? "Онлайн" : "Оффлайн"}
              </span>
            </button>

            <button
              type="button"
              className={styles.revokeInlineButton}
              onClick={() => onRevokeDevice(device.name)}
            >
              Отозвать
            </button>
          </div>

          {expandedDeviceName === device.name ? (
            <div className={styles.deviceExpanded}>
              <div className={styles.deviceInfoGrid}>
                <div className={styles.infoTile}>
                  <span>IP</span>
                  <strong>{device.ip}</strong>
                </div>
                <div className={styles.infoTile}>
                  <span>Последняя активность</span>
                  <strong>{device.lastSeen}</strong>
                </div>
                <div className={styles.infoTile}>
                  <span>Платформа</span>
                  <strong>{device.meta.split(" · ")[0]}</strong>
                </div>
                <div className={styles.infoTile}>
                  <span>Клиент</span>
                  <strong>{device.meta.split(" · ")[1] ?? device.meta}</strong>
                </div>
              </div>
            </div>
          ) : null}
        </article>
      ))}
    </div>
  );
}
