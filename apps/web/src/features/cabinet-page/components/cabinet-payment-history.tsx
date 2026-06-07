import styles from "./cabinet-page.module.css";
import type { CabinetPaymentHistoryEntry } from "./cabinet-models";

type CabinetPaymentHistoryProps = {
  entries: readonly CabinetPaymentHistoryEntry[];
  pendingPayment: CabinetPaymentHistoryEntry | null;
};

function resolvePaymentStatusLabel(status: string) {
  if (status === "paid") {
    return "Оплачен";
  }
  if (status === "pending") {
    return "Ожидает оплаты";
  }
  if (status === "failed") {
    return "Ошибка";
  }
  if (status === "canceled") {
    return "Отменен";
  }
  return status;
}

export function CabinetPaymentHistory({
  entries,
  pendingPayment,
}: CabinetPaymentHistoryProps) {
  return (
    <article className={styles.subscriptionPanel}>
      <div className={styles.panelHead}>
        <div>
          <div className={styles.panelTitle}>История оплат</div>
          <div className={styles.panelSub}>Последние транзакции и их статус</div>
        </div>
      </div>
      <div className={styles.panelBody}>
        {pendingPayment ? (
          <div className={styles.pendingPaymentCard}>
            <strong>Ожидающий платеж: {pendingPayment.planName}</strong>
            <span>{pendingPayment.amountRub} RUB</span>
            <span>Создан: {pendingPayment.createdAt}</span>
          </div>
        ) : null}

        {entries.length === 0 ? (
          <div className={styles.emptyState}>
            <strong>Оплат пока нет</strong>
            <p>После первой покупки здесь появится история транзакций.</p>
          </div>
        ) : (
          <div className={styles.historyList}>
            {entries.map((entry) => (
              <div key={entry.id} className={styles.historyRow}>
                <div>
                  <strong>{entry.planName}</strong>
                  <span>{entry.createdAt}</span>
                </div>
                <div>
                  <strong>{entry.amountRub} RUB</strong>
                  <span>{resolvePaymentStatusLabel(entry.status)}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </article>
  );
}
