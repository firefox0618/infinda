import styles from "./cabinet-page.module.css";
import type { CabinetSubscriptionHistoryEntry } from "./cabinet-models";

type CabinetSubscriptionHistoryProps = {
  entries: readonly CabinetSubscriptionHistoryEntry[];
};

function resolveEventLabel(eventType: CabinetSubscriptionHistoryEntry["eventType"]) {
  if (eventType === "trial_started") {
    return "Триал";
  }
  if (eventType === "activated") {
    return "Активация";
  }
  return "Продление";
}

export function CabinetSubscriptionHistory({
  entries,
}: CabinetSubscriptionHistoryProps) {
  return (
    <article className={styles.subscriptionPanel}>
      <div className={styles.panelHead}>
        <div>
          <div className={styles.panelTitle}>История подписки</div>
          <div className={styles.panelSub}>Активации, триал и предыдущие продления</div>
        </div>
      </div>
      <div className={styles.panelBody}>
        {entries.length === 0 ? (
          <div className={styles.emptyState}>
            <strong>История пока пуста</strong>
            <p>После активации или продления здесь появятся события жизненного цикла подписки.</p>
          </div>
        ) : (
          <div className={styles.historyList}>
            {entries.map((entry) => (
              <div key={entry.id} className={styles.historyRow}>
                <div>
                  <strong>{resolveEventLabel(entry.eventType)} · {entry.planName}</strong>
                  <span>{entry.createdAt}</span>
                </div>
                <div>
                  <strong>{entry.startsAt}</strong>
                  <span>до {entry.endsAt}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </article>
  );
}
