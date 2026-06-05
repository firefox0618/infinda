"use client";

import { useState } from "react";

import styles from "./cabinet-page.module.css";
import type { CabinetDevice } from "./cabinet-models";

import { DeviceIcon } from "./cabinet-icons";

type CabinetDevicesPanelProps = {
  devices: readonly CabinetDevice[];
  onRevokeDevice: (deviceId: number) => void;
};

export function CabinetDevicesPanel({
  devices,
  onRevokeDevice,
}: CabinetDevicesPanelProps) {
  const [expandedDeviceId, setExpandedDeviceId] = useState<number | null>(null);

  if (devices.length === 0) {
    return (
      <div className={styles.devicesList}>
        <article className={styles.deviceListItem}>
          <div className={styles.deviceExpanded}>
            <div className={styles.emptyState}>
              <strong>У вас пока нет подключенных устройств</strong>
              <p>После первого входа с клиента здесь появится список активных подключений.</p>
            </div>
          </div>
        </article>
      </div>
    );
  }

  return (
    <div className={styles.devicesList}>
      {devices.map((device, index) => (
        <article
          key={device.id}
          className={styles.deviceListItem}
          style={{ animationDelay: `${index * 90}ms` }}
        >
          <div className={styles.deviceRow}>
            <button
              type="button"
              className={styles.deviceSummaryButton}
              onClick={() =>
                setExpandedDeviceId((current) =>
                  current === device.id ? null : device.id,
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
              onClick={() => onRevokeDevice(device.id)}
            >
              Отозвать
            </button>
          </div>

          {expandedDeviceId === device.id ? (
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
                  <strong>{device.platformName}</strong>
                </div>
                <div className={styles.infoTile}>
                  <span>Клиент</span>
                  <strong>{device.clientName}</strong>
                </div>
              </div>
            </div>
          ) : null}
        </article>
      ))}
    </div>
  );
}
