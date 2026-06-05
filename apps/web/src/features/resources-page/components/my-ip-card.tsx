"use client";

import { useEffect, useState } from "react";

import styles from "./resources-page.module.css";

type IpState =
  | { status: "loading"; value: string }
  | { status: "success"; value: string }
  | { status: "error"; value: string };

export function MyIpCard() {
  const [ipState, setIpState] = useState<IpState>({
    status: "loading",
    value: "Определяем IP...",
  });

  useEffect(() => {
    let isMounted = true;

    const loadIp = async () => {
      try {
        const response = await fetch("https://api.ipify.org?format=json");

        if (!response.ok) {
          throw new Error("Failed to load IP");
        }

        const data = (await response.json()) as { ip?: string };

        if (!isMounted) {
          return;
        }

        setIpState({
          status: "success",
          value: data.ip ?? "IP не получен",
        });
      } catch {
        if (!isMounted) {
          return;
        }

        setIpState({
          status: "error",
          value: "Не удалось определить IP",
        });
      }
    };

    void loadIp();

    return () => {
      isMounted = false;
    };
  }, []);

  const refreshIp = async () => {
    setIpState({
      status: "loading",
      value: "Обновляем IP...",
    });

    try {
      const response = await fetch("https://api.ipify.org?format=json", {
        cache: "no-store",
      });

      if (!response.ok) {
        throw new Error("Failed to refresh IP");
      }

      const data = (await response.json()) as { ip?: string };

      setIpState({
        status: "success",
        value: data.ip ?? "IP не получен",
      });
    } catch {
      setIpState({
        status: "error",
        value: "Не удалось определить IP",
      });
    }
  };

  return (
    <div className={styles.ipBlock}>
      <div className={styles.ipLabel}>Текущий IP</div>
      <div
        className={`${styles.ipValue} ${
          ipState.status === "error" ? styles.ipValueError : ""
        }`}
      >
        {ipState.value}
      </div>
      <div className={styles.ipHint}>
        {ipState.status === "success"
          ? "IP получен из внешнего сервиса и обновляется при открытии страницы."
          : "Если IP не отображается, проверьте подключение к сети и обновите страницу."}
      </div>
      <button type="button" className={styles.ipRefreshButton} onClick={refreshIp}>
        Обновить
      </button>
    </div>
  );
}
