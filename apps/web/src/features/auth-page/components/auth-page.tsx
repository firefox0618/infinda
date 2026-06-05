"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { fetchCurrentUser } from "@/shared/auth/auth-client";
import { clearAuthSession, readAuthToken } from "@/shared/auth/auth-storage";

import styles from "./auth-page.module.css";

import { AuthPanel } from "./auth-panel";

export function AuthPage() {
  const router = useRouter();
  const [isLoaderHidden, setIsLoaderHidden] = useState(false);

  useEffect(() => {
    const hideTimer = window.setTimeout(() => {
      setIsLoaderHidden(true);
    }, 550);

    return () => window.clearTimeout(hideTimer);
  }, []);

  useEffect(() => {
    const token = readAuthToken();

    if (!token) {
      return;
    }

    let isCancelled = false;

    void fetchCurrentUser(token)
      .then(() => {
        if (!isCancelled) {
          router.replace("/cabinet");
        }
      })
      .catch(() => {
        if (!isCancelled) {
          clearAuthSession();
        }
      });

    return () => {
      isCancelled = true;
    };
  }, [router]);

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
