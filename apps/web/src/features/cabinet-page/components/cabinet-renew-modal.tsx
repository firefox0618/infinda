import styles from "./cabinet-page.module.css";
import type { CabinetSubscriptionPlan } from "../api/cabinet-client";

type CabinetRenewModalProps = {
  isOpen: boolean;
  plans: readonly CabinetSubscriptionPlan[];
  actionState: "idle" | "loading" | "success" | "error";
  actionMessage: string;
  onClose: () => void;
  onCheckout: (planCode: string) => void;
};

export function CabinetRenewModal({
  isOpen,
  plans,
  actionState,
  actionMessage,
  onClose,
  onCheckout,
}: CabinetRenewModalProps) {
  if (!isOpen) {
    return null;
  }

  return (
    <div
      className={styles.modalOverlay}
      role="presentation"
      onClick={onClose}
    >
      <div
        className={styles.modalCard}
        role="dialog"
        aria-modal="true"
        aria-labelledby="renew-modal-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className={styles.modalHead}>
          <div>
            <h2 id="renew-modal-title" className={styles.modalTitle}>
              Продлить подписку
            </h2>
            <p className={styles.modalText}>
              Выберите тариф. Подписка активируется сразу после подтверждения.
            </p>
          </div>
          <button
            type="button"
            className={styles.modalCloseButton}
            onClick={onClose}
          >
            Закрыть
          </button>
        </div>

        <div className={styles.tariffGrid}>
          {plans.map((tariff) => (
            <article key={tariff.code} className={styles.tariffCard}>
              <div className={styles.tariffTitle}>{tariff.title}</div>
              <div className={styles.tariffPrice}>{tariff.priceRub} ₽</div>
              <div className={styles.tariffNote}>{tariff.description}</div>
              <button
                type="button"
                className={styles.primaryButton}
                disabled={actionState === "loading"}
                onClick={() => onCheckout(tariff.code)}
              >
                {actionState === "loading" ? "Оформление…" : "Перейти к оплате"}
              </button>
            </article>
          ))}
        </div>
        {actionState !== "idle" ? (
          <p className={styles.modalText}>{actionMessage}</p>
        ) : null}
      </div>
    </div>
  );
}
