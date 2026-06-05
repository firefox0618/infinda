import styles from "./cabinet-page.module.css";
import type {
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
    status: "none" | "trial" | "active" | "expired";
    isTrial: boolean;
    mainLink: string | null;
  } | null;
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
  devices,
  copyLabel,
  onCopyMainLink,
  onOpenRenew,
  onOpenTab,
}: CabinetOverviewPanelProps) {
  const subscriptionTitle =
    subscription?.status === "expired"
      ? subscription.isTrial
        ? "Триал закончился"
        : "Подписка закончилась"
      : subscription?.status === "none"
        ? "У вас пока нет активной подписки"
        : "Основная подписка";

  const subscriptionNote =
    subscription?.status === "expired"
      ? "Оформите новый доступ, чтобы снова подключать устройства и маршруты."
      : subscription?.status === "none"
        ? "Оформите подписку, чтобы получить ссылку подключения и маршруты."
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
            {subscription && subscription.mainLink && subscription.status !== "expired" ? (
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
                      <strong>{device.name}</strong>
                      <span>{device.meta}</span>
                    </div>
                  </div>
                  <span>{device.meta.split(" · ")[0]}</span>
                  <span>{device.ip}</span>
                  <span>{device.lastSeen}</span>
                  <span
                    className={`${styles.tableStatus} ${
                      device.status === "online"
                        ? styles.tableStatusOnline
                        : styles.tableStatusOffline
                    }`}
                  >
                    {device.status}
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
                    subscription?.status === "trial" || subscription?.status === "active"
                      ? styles.statusValueActive
                      : subscription?.status === "expired"
                        ? styles.statusValueWarning
                        : styles.statusValueMuted
                  }`}
                >
                  {subscription?.status === "trial"
                    ? "trial"
                    : subscription?.status === "active"
                      ? "active"
                      : subscription?.status === "expired"
                        ? "expired"
                        : "none"}
                </strong>
              </div>
              <div className={styles.statusRow}>
                <span>Маршрутизация</span>
                <strong>auto</strong>
              </div>
              <div className={styles.statusRow}>
                <span>Личный кабинет</span>
                <strong>online</strong>
              </div>
              <div className={styles.statusRow}>
                <span>Поддержка</span>
                <strong>online</strong>
              </div>
            </div>
          </div>
        </article>

        <article className={styles.noticeCard}>
          <strong>
            {subscription?.status === "expired" || subscription?.status === "none"
              ? "Доступ пока не активирован"
              : "Маршруты работают автоматически"}
          </strong>
          <p>
            {subscription?.status === "expired"
              ? "Текущий доступ завершился. Оформите новую подписку, чтобы снова использовать защищенные маршруты."
              : subscription?.status === "none"
                ? "После оформления подписки здесь появятся рабочая ссылка, маршруты и доступные лимиты устройств."
                : "Привычные сайты открываются напрямую, а нужный трафик проходит через защищенный маршрут."}
          </p>
        </article>
      </aside>
    </div>
  );
}
