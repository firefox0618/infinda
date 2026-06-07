"use client";

import { useState } from "react";

import styles from "./cabinet-page.module.css";
import type { CabinetDevice } from "./cabinet-models";

import { DeviceIcon } from "./cabinet-icons";

type CabinetDevicesPanelProps = {
  devices: readonly CabinetDevice[];
  actionMessage: string;
  actionState: "idle" | "success" | "error";
  onRevokeDevice: (deviceId: number, reason?: string) => void;
};

export function CabinetDevicesPanel({
  actionMessage,
  actionState,
  devices,
  onRevokeDevice,
}: CabinetDevicesPanelProps) {
  const [expandedDeviceId, setExpandedDeviceId] = useState<number | null>(null);
  const [revokeReason, setRevokeReason] = useState<Record<number, string>>({});

  const currentDevices = devices.filter((device) => device.isCurrent);
  const activeDevices = devices.filter(
    (device) => !device.isCurrent && device.computedStatus === "active",
  );
  const staleDevices = devices.filter((device) => device.computedStatus === "stale");
  const revokedDevices = devices.filter((device) => device.computedStatus === "revoked");

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

  const groups = [
    { key: "current", title: "Текущее устройство", devices: currentDevices },
    { key: "active", title: "Активные устройства", devices: activeDevices },
    { key: "stale", title: "Давно неактивные", devices: staleDevices },
    { key: "revoked", title: "Отозванные", devices: revokedDevices },
  ] as const;

  return (
    <div className={styles.deviceSectionStack}>
      {actionMessage ? (
        <div
          className={`${styles.deviceActionBanner} ${
            actionState === "error" ? styles.deviceActionBannerError : ""
          }`}
        >
          {actionMessage}
        </div>
      ) : null}

      {groups.map((group) =>
        group.devices.length > 0 ? (
          <section key={group.key} className={styles.deviceGroup}>
            <div className={styles.deviceGroupTitle}>{group.title}</div>
            <div className={styles.devicesList}>
              {group.devices.map((device, index) => (
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
                          <div className={styles.deviceName}>{device.displayName}</div>
                          <div className={styles.deviceMeta}>
                            {device.meta}
                            {device.isCurrent ? " · текущий сеанс" : ""}
                          </div>
                        </div>
                      </div>
                      <span
                        className={`${styles.deviceStatus} ${
                          device.computedStatus === "active"
                            ? styles.deviceStatusOnline
                            : styles.deviceStatusOffline
                        }`}
                      >
                        {device.computedStatus}
                      </span>
                    </button>

                    {device.computedStatus !== "revoked" ? (
                      <button
                        type="button"
                        className={styles.revokeInlineButton}
                        onClick={() => onRevokeDevice(device.id, revokeReason[device.id])}
                      >
                        Отозвать
                      </button>
                    ) : null}
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
                          <strong>{device.platform}</strong>
                        </div>
                        <div className={styles.infoTile}>
                          <span>Клиент</span>
                          <strong>{device.client}</strong>
                        </div>
                      </div>

                      {device.computedStatus !== "revoked" ? (
                        <div className={styles.revokeForm}>
                          <label className={styles.revokeReasonLabel}>
                            Причина отзыва
                            <input
                              type="text"
                              className={styles.revokeReasonInput}
                              value={revokeReason[device.id] ?? ""}
                              onChange={(event) =>
                                setRevokeReason((current) => ({
                                  ...current,
                                  [device.id]: event.target.value,
                                }))
                              }
                              placeholder="Например: старое устройство или потеряно"
                            />
                          </label>
                        </div>
                      ) : device.revokedReason ? (
                        <div className={styles.revokedMeta}>
                          Причина: {device.revokedReason}
                        </div>
                      ) : null}
                    </div>
                  ) : null}
                </article>
              ))}
            </div>
          </section>
        ) : null,
      )}
    </div>
  );
}
