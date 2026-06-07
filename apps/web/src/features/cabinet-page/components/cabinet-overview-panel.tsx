import styles from "./cabinet-page.module.css";
import type {
  CabinetAccessState,
  CabinetDevice,
  CabinetOverviewStat,
  CabinetTab,
} from "./cabinet-models";

import {
  CopyIcon,
  DeviceIcon,
  SparkIcon,
  SupportPulseIcon,
} from "./cabinet-icons";

type CabinetOverviewPanelProps = {
  stats: readonly CabinetOverviewStat[];
  subscription: {
    status: "none" | "trial" | "active" | "expired" | "pending_payment";
    isTrial: boolean;
    mainLink: string | null;
  } | null;
  accessState: CabinetAccessState | null;
  devices: readonly CabinetDevice[];
  copyLabel: string;
  onCopyMainLink: () => void;
  onOpenRenew: () => void;
  onOpenTab: (tab: Extract<CabinetTab, "subscription" | "devices" | "support">) => void;
};

const quickActions = [
  {
    title: "Проверить ссылку",
    note: "перейти к подписке",
    tab: "subscription" as const,
  },
  {
    title: "Управлять устройствами",
    note: "отозвать доступ",
    tab: "devices" as const,
  },
  {
    title: "Открыть поддержку",
    note: "написать в чат",
    tab: "support" as const,
  },
];

export function CabinetOverviewPanel({
  stats,
  subscription,
  accessState,
  devices,
  copyLabel,
  onCopyMainLink,
  onOpenRenew,
  onOpenTab,
}: CabinetOverviewPanelProps) {
  const accessStateLabel =
    accessState?.status === "active"
      ? "active"
      : accessState?.status === "expired"
        ? "expired"
        : accessState?.status === "pending_payment"
          ? "pending"
          : accessState?.status === "device_limit_exceeded"
            ? "device limit"
            : accessState?.status === "server_unavailable"
              ? "server unavailable"
              : "restricted";

  const subscriptionTitle =
    subscription?.status === "expired"
      ? subscription.isTrial
        ? "Триал закончился"
        : "Подписка закончилась"
      : subscription?.status === "none"
        ? "У вас пока нет активной подписки"
        : subscription?.status === "pending_payment"
          ? "Ожидаем подтверждение оплаты"
        : "Основная подписка";

  const subscriptionNote =
    subscription?.status === "expired"
      ? "Оформите новый доступ, чтобы снова подключать устройства и маршруты."
      : subscription?.status === "none"
        ? "Оформите подписку, чтобы получить ссылку подключения и маршруты."
        : subscription?.status === "pending_payment"
          ? "После подтверждения оплаты появятся рабочая ссылка и маршруты."
        : "Ссылка для подключения устройств";

  return (
    <div className={styles.dashboardGrid}>
      <div className={styles.dashboardMain}>
        <div className={styles.metricsGrid}>
        {stats.map((stat, index) => (
          <article
            key={stat.title}
            className={styles.metricCard}
            style={{ animationDelay: `${index * 90}ms` }}
          >
            <div className={styles.metricLabel}>{stat.title}</div>
            <div className={styles.metricValue}>{stat.value}</div>
            <div className={styles.metricNote}>{stat.note}</div>
          </article>
        ))}
        </div>

        <article className={styles.dashboardPanel}>
          <div className={styles.panelHead}>
            <div>
              <div className={styles.panelTitle}>{subscriptionTitle}</div>
              <div className={styles.panelSub}>{subscriptionNote}</div>
            </div>
            <span className={styles.panelHeadAccent} aria-hidden="true">
              <SparkIcon />
            </span>
          </div>

          <div className={styles.panelBody}>
            {subscription &&
            subscription.mainLink &&
            subscription.status !== "expired" &&
            subscription.status !== "pending_payment" ? (
              <div className={styles.subscriptionRow}>
                <div className={styles.subscriptionLink}>{subscription.mainLink}</div>
                <button
                  type="button"
                  className={styles.copyButton}
                  onClick={onCopyMainLink}
                >
                  <CopyIcon />
                  <span>{copyLabel}</span>
                </button>
              </div>
            ) : (
              <div className={styles.emptyState}>
                <strong>{subscriptionTitle}</strong>
                <p>{subscriptionNote}</p>
                <div>
                  <button
                    type="button"
                    className={styles.primaryButton}
                    onClick={onOpenRenew}
                  >
                    Оформить подписку
                  </button>
                </div>
              </div>
            )}
          </div>
        </article>

        <article className={styles.dashboardPanel}>
          <div className={styles.panelHead}>
            <div>
              <div className={styles.panelTitle}>Устройства</div>
              <div className={styles.panelSub}>Последняя активность подключений</div>
            </div>
            <button
              type="button"
              className={styles.topButton}
              onClick={() => onOpenTab("devices")}
            >
              Открыть
            </button>
          </div>

          <div className={styles.panelBody}>
            <div className={styles.deviceTable}>
              <div className={styles.deviceTableHead}>
                <span>Устройство</span>
                <span>Платформа</span>
                <span>IP</span>
                <span>Активность</span>
                <span>Статус</span>
              </div>

              {devices.length === 0 ? (
                <div className={styles.deviceTableEmpty}>
                  Подключенные устройства появятся после первого входа с клиента.
                </div>
              ) : null}

              {devices.map((device) => (
                <div key={device.id} className={styles.deviceTableRow}>
                  <div className={styles.deviceTableName}>
                    <span className={styles.deviceTablePlatformIcon} aria-hidden="true">
                      <DeviceIcon kind={device.icon} />
                    </span>
                    <div>
                      <strong>{device.displayName}</strong>
                      <span>{device.meta}</span>
                    </div>
                  </div>
                  <span>{device.meta.split(" · ")[0]}</span>
                  <span>{device.ip}</span>
                  <span>{device.lastSeen}</span>
                  <span
                    className={`${styles.tableStatus} ${
                      device.computedStatus === "active"
                        ? styles.tableStatusOnline
                        : styles.tableStatusOffline
                    }`}
                  >
                    {device.isCurrent ? "current" : device.computedStatus}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </article>
      </div>

      <aside className={styles.dashboardAside}>
        <article className={styles.dashboardPanel}>
          <div className={styles.panelHead}>
            <div>
              <div className={styles.panelTitle}>Быстрые действия</div>
              <div className={styles.panelSub}>Частые операции</div>
            </div>
          </div>

          <div className={styles.panelBody}>
            <div className={styles.quickActionList}>
              {quickActions.map((action) => (
                <button
                  key={action.title}
                  type="button"
                  className={styles.quickActionRow}
                  onClick={() => onOpenTab(action.tab)}
                >
                  <span className={styles.quickActionIcon} aria-hidden="true">
                    {action.tab === "subscription" ? (
                      <CopyIcon />
                    ) : action.tab === "devices" ? (
                      <DeviceIcon kind="mobile" />
                    ) : (
                      <SupportPulseIcon />
                    )}
                  </span>
                  <span className={styles.quickActionCopy}>
                    <span className={styles.quickActionTitle}>{action.title}</span>
                    <span className={styles.quickActionNote}>{action.note}</span>
                  </span>
                  <span className={styles.quickActionArrow} aria-hidden="true">
                    ›
                  </span>
                </button>
              ))}
            </div>
          </div>
        </article>

        <article className={styles.dashboardPanel}>
          <div className={styles.panelHead}>
            <div>
              <div className={styles.panelTitle}>Состояние</div>
              <div className={styles.panelSub}>Основные сервисы</div>
            </div>
          </div>

          <div className={styles.panelBody}>
            <div className={styles.statusList}>
              <div className={styles.statusRow}>
                <span>Подписка</span>
                <strong
                  className={`${styles.statusValue} ${
                    accessState?.status === "active"
                      ? styles.statusValueActive
                      : accessState?.status === "expired" ||
                          accessState?.status === "pending_payment" ||
                          accessState?.status === "device_limit_exceeded" ||
                          accessState?.status === "server_unavailable"
                        ? styles.statusValueWarning
                        : styles.statusValueMuted
                  }`}
                >
                  {accessStateLabel}
                </strong>
              </div>
              <div className={styles.statusRow}>
                <span>Маршрутизация</span>
                <strong>{accessState ? accessState.availableRouteCount : 0}</strong>
              </div>
              <div className={styles.statusRow}>
                <span>Личный кабинет</span>
                <strong>online</strong>
              </div>
              <div className={styles.statusRow}>
                <span>Поддержка</span>
                <strong>online</strong>
              </div>
              <div className={styles.statusRow}>
                <span>Устройства</span>
                <strong>
                  {accessState
                    ? `${accessState.activeDeviceCount}/${accessState.allowedDeviceCount}`
                    : devices.length}
                </strong>
              </div>
            </div>
          </div>
        </article>

        <article className={styles.noticeCard}>
          <strong>
            {accessState?.status === "expired" ||
            accessState?.status === "restricted" ||
            accessState?.status === "pending_payment"
              ? "Доступ пока не активирован"
              : "Маршруты работают автоматически"}
          </strong>
          <p>
            {accessState?.status === "expired"
              ? "Текущий доступ завершился. Оформите новую подписку, чтобы снова использовать защищенные маршруты."
              : accessState?.status === "pending_payment"
                ? "Ожидаем подтверждение оплаты. После этого доступ и маршруты активируются автоматически."
                : accessState?.status === "restricted"
                ? "После оформления подписки здесь появятся рабочая ссылка, маршруты и доступные лимиты устройств."
                : accessState?.status === "device_limit_exceeded"
                  ? "Количество устройств превысило лимит подписки. Отзовите лишние подключения, чтобы восстановить доступ."
                  : accessState?.status === "server_unavailable"
                    ? "Назначенные серверы сейчас недоступны. После восстановления маршруты снова станут активны."
                : "Привычные сайты открываются напрямую, а нужный трафик проходит через защищенный маршрут."}
          </p>
        </article>
      </aside>
    </div>
  );
}
