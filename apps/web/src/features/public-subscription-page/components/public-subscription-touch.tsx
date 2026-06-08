"use client";

import { useEffect, useEffectEvent, useState } from "react";

import type {
  PublicSubscriptionTouchDto,
  PublicSubscriptionTouchRequestDto,
} from "@infinda/shared/contracts/public-subscription";

import { ensurePublicDeviceKey } from "./public-device-key";
import styles from "./public-subscription-page.module.css";

type PublicSubscriptionTouchProps = {
  token: string;
  onTouched?: () => void;
};

type TouchState =
  | { status: "idle" | "loading" }
  | { status: "success"; payload: PublicSubscriptionTouchDto }
  | { status: "error"; message: string };

function resolveTouchPayload(): PublicSubscriptionTouchRequestDto {
  if (typeof window === "undefined") {
    return {};
  }

  const platform = window.navigator.platform || "";
  const userAgent = window.navigator.userAgent || "";
  const isMobile = /iphone|ipad|android|mobile/i.test(userAgent);
  const isLaptop = /mac|win|linux/i.test(platform) || /macintosh|windows|linux/i.test(userAgent);
  return {
    device_name: platform ? `${platform} device` : "Current device",
    platform,
    client: "Happ",
    icon: isMobile ? "mobile" : isLaptop ? "laptop" : "desktop",
  };
}

export function PublicSubscriptionTouch({ token, onTouched }: PublicSubscriptionTouchProps) {
  const [state, setState] = useState<TouchState>({ status: "idle" });
  const handleTouched = useEffectEvent(() => {
    onTouched?.();
  });

  useEffect(() => {
    const storageKey = `public-subscription-touch:${token}`;
    if (typeof window !== "undefined" && window.sessionStorage.getItem(storageKey) === "done") {
      return;
    }

    let cancelled = false;
    const controller = new AbortController();

    async function runTouch() {
      setState({ status: "loading" });
      try {
        const deviceKey = ensurePublicDeviceKey(token);
        const response = await fetch(`/api/subscription/public/${token}/touch`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Device-Key": deviceKey,
          },
          body: JSON.stringify(resolveTouchPayload()),
          cache: "no-store",
          signal: controller.signal,
        });
        const payload = (await response.json()) as
          | PublicSubscriptionTouchDto
          | { error?: { message?: string } };
        if (!response.ok) {
          throw new Error(payload && "error" in payload ? payload.error?.message || "Touch failed." : "Touch failed.");
        }
        if (cancelled) {
          return;
        }
        window.sessionStorage.setItem(storageKey, "done");
        setState({ status: "success", payload: payload as PublicSubscriptionTouchDto });
        handleTouched();
      } catch (error) {
        if (cancelled || controller.signal.aborted) {
          return;
        }
        setState({
          status: "error",
          message: error instanceof Error ? error.message : "Touch failed.",
        });
      }
    }

    void runTouch();

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [token]);

  if (state.status === "idle" || state.status === "loading") {
    return (
      <div className={styles.touchBanner}>
        Проверяем текущее устройство и подготавливаем персональный доступ.
      </div>
    );
  }

  if (state.status === "error") {
    return (
      <div className={`${styles.touchBanner} ${styles.touchBannerMuted}`}>
        Не удалось автоматически привязать устройство: {state.message}
      </div>
    );
  }

  if (state.status !== "success") {
    return null;
  }

  const payload = state.payload;

  return (
    <div className={`${styles.touchBanner} ${styles.touchBannerActive}`}>
      {payload.created ? "Устройство создано" : "Устройство обновлено"}:{" "}
      {payload.device.display_name}. Запущено операций:{" "}
      {payload.scheduled_operation_count}, ошибок:{" "}
      {payload.failed_operation_count}.
    </div>
  );
}
