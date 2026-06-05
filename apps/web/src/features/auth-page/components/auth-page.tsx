 "use client";

import { useEffect, useState } from "react";

import styles from "./auth-page.module.css";

import { AuthPanel } from "./auth-panel";

export function AuthPage() {
  const [isLoaderHidden, setIsLoaderHidden] = useState(false);

  useEffect(() => {
    const hideTimer = window.setTimeout(() => {
      setIsLoaderHidden(true);
    }, 550);

    return () => window.clearTimeout(hideTimer);
  }, []);

  return (
    <div className={styles.page}>
      <div
        className={`${styles.pageLoader} ${
          isLoaderHidden ? styles.pageLoaderHidden : ""
        }`}
        aria-hidden={isLoaderHidden}
      >
        <div className={styles.loaderShell}>
          <div className={styles.loaderOrbit} />
          <div className={styles.loaderCard}>
            <div className={styles.loaderLogo}>Λ</div>
            <div className={styles.loaderText}>INFINDA</div>
            <div className={styles.loaderStatus}>подготовка доступа</div>
          </div>
        </div>
      </div>

      <div className={styles.background} aria-hidden="true" />
      <div className={styles.container}>
        <AuthPanel />
      </div>
    </div>
  );
}
