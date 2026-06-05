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
  mainLink: string;
  devices: readonly CabinetDevice[];
  copyLabel: string;
  onCopyMainLink: () => void;
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
  mainLink,
  devices,
  copyLabel,
  onCopyMainLink,
  onOpenTab,
}: CabinetOverviewPanelProps) {
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
              <div className={styles.panelTitle}>Основная подписка</div>
              <div className={styles.panelSub}>Ссылка для подключения устройств</div>
            </div>
            <span className={styles.panelHeadAccent} aria-hidden="true">
              <SparkIcon />
            </span>
          </div>

          <div className={styles.panelBody}>
            <div className={styles.subscriptionRow}>
              <div className={styles.subscriptionLink}>{mainLink}</div>
              <button
                type="button"
                className={styles.copyButton}
                onClick={onCopyMainLink}
              >
                <CopyIcon />
                <span>{copyLabel}</span>
              </button>
            </div>
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
                <strong>active</strong>
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
          <strong>Маршруты работают автоматически</strong>
          <p>
            Привычные сайты открываются напрямую, а нужный трафик проходит
            через защищенный маршрут.
          </p>
        </article>
      </aside>
    </div>
  );
}
