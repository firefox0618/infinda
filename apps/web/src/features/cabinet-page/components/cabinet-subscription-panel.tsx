import styles from "./cabinet-page.module.css";

import { CopyIcon } from "./cabinet-icons";

type CountryLink = {
  code: string;
  label: string;
  url: string;
};

type SubscriptionDetail = {
  label: string;
  value: string;
};

type CabinetSubscriptionPanelProps = {
  mainLink: string;
  countries: readonly CountryLink[];
  selectedCountryCode: string;
  selectedCountryUrl: string;
  details: readonly SubscriptionDetail[];
  mainCopyLabel: string;
  serverCopyLabel: string;
  onOpenRenew: () => void;
  onSelectCountry: (countryCode: string) => void;
  onCopyMainLink: () => void;
  onCopyCountryLink: () => void;
};

export function CabinetSubscriptionPanel({
  mainLink,
  countries,
  selectedCountryCode,
  selectedCountryUrl,
  details,
  mainCopyLabel,
  serverCopyLabel,
  onOpenRenew,
  onSelectCountry,
  onCopyMainLink,
  onCopyCountryLink,
}: CabinetSubscriptionPanelProps) {
  return (
    <div className={styles.subscriptionLayout}>
      <article className={styles.subscriptionPanel}>
        <div className={styles.panelHead}>
          <div>
            <div className={styles.panelTitle}>Ссылка подписки</div>
            <div className={styles.panelSub}>Один общий доступ для всех клиентов</div>
          </div>
          <button
            type="button"
            className={styles.topButton}
            onClick={onOpenRenew}
          >
            Продлить
          </button>
        </div>
        <div className={styles.panelBody}>
          <div className={styles.subscriptionBlock}>
            <div className={styles.subscriptionBlockLabel}>Основной URL</div>
            <div className={styles.compactSubscriptionRow}>
              <div className={styles.compactUrlPanel}>{mainLink}</div>
              <button
                type="button"
                className={styles.copyButton}
                onClick={onCopyMainLink}
              >
                <CopyIcon />
                <span>{mainCopyLabel}</span>
              </button>
            </div>
          </div>
        </div>
      </article>

      <div className={styles.subscriptionBottomGrid}>
        <article className={styles.subscriptionPanel}>
          <div className={styles.panelHead}>
            <div>
              <div className={styles.panelTitle}>Отдельный маршрут</div>
              <div className={styles.panelSub}>Ссылка под конкретную страну</div>
            </div>
          </div>
          <div className={styles.panelBody}>
            <div className={styles.countryButtons}>
              {countries.map((country) => (
                <button
                  key={country.code}
                  type="button"
                  className={`${styles.countryButton} ${
                    selectedCountryCode === country.code
                      ? styles.countryButtonActive
                      : ""
                  }`}
                  onClick={() => onSelectCountry(country.code)}
                >
                  {country.label}
                </button>
              ))}
            </div>
            <div className={styles.subscriptionBlock}>
              <div className={styles.subscriptionBlockLabel}>Выбранный маршрут</div>
              <div className={styles.compactSubscriptionRow}>
                <div className={styles.compactUrlPanel}>{selectedCountryUrl}</div>
                <button
                  type="button"
                  className={styles.secondaryButton}
                  onClick={onCopyCountryLink}
                >
                  <CopyIcon />
                  <span>{serverCopyLabel}</span>
                </button>
              </div>
            </div>
          </div>
        </article>

        <article className={styles.subscriptionPanel}>
          <div className={styles.panelHead}>
            <div>
              <div className={styles.panelTitle}>Параметры подписки</div>
              <div className={styles.panelSub}>Срок, устройства и доступ</div>
            </div>
          </div>
          <div className={styles.panelBody}>
            <div className={styles.detailsList}>
              {details.map((detail) => (
                <div key={detail.label} className={styles.detailRow}>
                  <span>{detail.label}</span>
                  <strong>{detail.value}</strong>
                </div>
              ))}
            </div>
          </div>
        </article>
      </div>
    </div>
  );
}
