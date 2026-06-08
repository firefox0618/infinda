"use client";

import { useState } from "react";

import styles from "./public-subscription-page.module.css";

type HappWrapperActionsProps = {
  happDeepLink: string;
  subscriptionUrl: string;
};

export function HappWrapperActions({
  happDeepLink,
  subscriptionUrl,
}: HappWrapperActionsProps) {
  const [copyStatus, setCopyStatus] = useState(
    "Если Happ не открылся, скопируйте feed и вставьте его в приложение вручную.",
  );

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(subscriptionUrl);
      setCopyStatus("Feed скопирован. Теперь его можно вставить в Happ вручную.");
    } catch {
      setCopyStatus("Автокопирование не сработало. Скопируйте feed из блока ниже вручную.");
    }
  }

  return (
    <div className={styles.wrapperActionsStack}>
      <div className={styles.wrapperActionGroup}>
        <a className={styles.linkBadge} href={happDeepLink}>
          Открыть Happ
        </a>
        <button type="button" className={styles.linkBadgeSecondaryButton} onClick={handleCopy}>
          Скопировать feed
        </button>
      </div>
      <p className={styles.wrapperHint}>
        На Linux браузер может не открыть `happ://`, если протокол не зарегистрирован в системе.
        В этом случае используйте копирование и импортируйте feed вручную.
      </p>
      <p className={styles.wrapperStatus}>{copyStatus}</p>
    </div>
  );
}
