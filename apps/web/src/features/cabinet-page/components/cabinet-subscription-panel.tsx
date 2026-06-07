import styles from "./cabinet-page.module.css";

import { CopyIcon } from "./cabinet-icons";
import { CabinetPaymentHistory } from "./cabinet-payment-history";
import { CabinetSubscriptionHistory } from "./cabinet-subscription-history";
import type {
  CabinetPaymentHistoryEntry,
  CabinetSubscriptionHistoryEntry,
} from "./cabinet-models";

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
  subscription: {
    status: "none" | "trial" | "active" | "expired" | "pending_payment";
    isTrial: boolean;
    mainLink: string | null;
    countries: readonly CountryLink[];
    paymentHistory: readonly CabinetPaymentHistoryEntry[];
    subscriptionHistory: readonly CabinetSubscriptionHistoryEntry[];
    pendingPayment: CabinetPaymentHistoryEntry | null;
  };
  selectedCountryCode: string;
  selectedCountryUrl: string | null;
  details: readonly SubscriptionDetail[];
  mainCopyLabel: string;
  serverCopyLabel: string;
  onOpenRenew: () => void;
  onSelectCountry: (countryCode: string) => void;
  onCopyMainLink: () => void;
  onCopyCountryLink: () => void;
};

export function CabinetSubscriptionPanel({
  subscription,
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
  if (subscription.status === "none" || subscription.status === "pending_payment") {
    return (
      <div className={styles.subscriptionLayout}>
        <article className={styles.subscriptionPanel}>
          <div className={styles.panelHead}>
            <div>
              <div className={styles.panelTitle}>Подписка</div>
              <div className={styles.panelSub}>
                {subscription.status === "pending_payment"
                  ? "Оплата создана, ожидаем подтверждение провайдера"
                  : "Ссылки и маршруты появятся после оформления доступа"}
              </div>
            </div>
          </div>
          <div className={styles.panelBody}>
            <div className={styles.emptyState}>
              <strong>
                {subscription.status === "pending_payment"
                  ? "Есть ожидающий платеж"
                  : "У вас пока нет активной подписки"}
              </strong>
              <p>
                {subscription.status === "pending_payment"
                  ? "После подтверждения оплаты здесь появятся активная подписка, ссылки и маршруты."
                  : "Оформите подписку, чтобы получить основную ссылку, маршруты по странам и лимит устройств."}
              </p>
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
          </div>
        </article>
        <CabinetPaymentHistory
          entries={subscription.paymentHistory}
          pendingPayment={subscription.pendingPayment}
        />
        <CabinetSubscriptionHistory entries={subscription.subscriptionHistory} />
      </div>
    );
  }

  const isExpired = subscription.status === "expired";
  const expiredTitle = subscription.isTrial ? "Триал закончился" : "Подписка закончилась";

  return (
    <div className={styles.subscriptionLayout}>
      {isExpired ? (
        <article className={styles.subscriptionPanel}>
          <div className={styles.panelHead}>
            <div>
              <div className={styles.panelTitle}>{expiredTitle}</div>
              <div className={styles.panelSub}>Оформите новый доступ, чтобы снова использовать рабочие ссылки</div>
            </div>
            <button
              type="button"
              className={styles.topButton}
              onClick={onOpenRenew}
            >
              Оформить подписку
            </button>
          </div>
          <div className={styles.panelBody}>
            <div className={styles.emptyState}>
              <strong>{expiredTitle}</strong>
              <p>Текущий доступ завершился. После продления снова станут доступны маршруты и подключение устройств.</p>
            </div>
          </div>
        </article>
      ) : null}

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
          {subscription.mainLink && !isExpired ? (
            <div className={styles.subscriptionBlock}>
              <div className={styles.subscriptionBlockLabel}>Основной URL</div>
              <div className={styles.compactSubscriptionRow}>
                <div className={styles.compactUrlPanel}>{subscription.mainLink}</div>
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
          ) : (
            <div className={styles.emptyState}>
              <strong>{expiredTitle}</strong>
              <p>Рабочая ссылка появится снова после продления подписки.</p>
            </div>
          )}
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
            {subscription.countries.length > 0 && !isExpired ? (
              <>
                <div className={styles.countryButtons}>
                  {subscription.countries.map((country) => (
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
              </>
            ) : (
              <div className={styles.emptyState}>
                <strong>{isExpired ? "Маршруты недоступны" : "Маршруты пока не подготовлены"}</strong>
                <p>
                  {isExpired
                    ? "После продления здесь снова появятся ссылки по странам."
                    : "Маршруты появятся после активации подписки."}
                </p>
              </div>
            )}
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

      <div className={styles.subscriptionBottomGrid}>
        <CabinetPaymentHistory
          entries={subscription.paymentHistory}
          pendingPayment={subscription.pendingPayment}
        />
        <CabinetSubscriptionHistory entries={subscription.subscriptionHistory} />
      </div>
    </div>
  );
}
