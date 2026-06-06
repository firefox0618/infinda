"use client";

import { useCallback, useState } from "react";

import { clearAuthSession, readAuthToken } from "@/shared/auth/auth-storage";
import { createCabinetSubscriptionCheckout } from "../api/cabinet-client";

type SubscriptionActionState = "idle" | "loading" | "success" | "error";

export function useCabinetSubscriptionActions(onAuthRequired: () => void) {
  const [isRenewModalOpen, setIsRenewModalOpen] = useState(false);
  const [subscriptionActionState, setSubscriptionActionState] =
    useState<SubscriptionActionState>("idle");
  const [subscriptionActionMessage, setSubscriptionActionMessage] = useState("");

  const resetSubscriptionActionState = useCallback(() => {
    setSubscriptionActionState("idle");
    setSubscriptionActionMessage("");
  }, []);

  const openRenewModal = useCallback(() => {
    resetSubscriptionActionState();
    setIsRenewModalOpen(true);
  }, [resetSubscriptionActionState]);

  const closeRenewModal = useCallback(() => {
    setIsRenewModalOpen(false);
    resetSubscriptionActionState();
  }, [resetSubscriptionActionState]);

  const handleSubscriptionCheckout = useCallback(
    async (planCode: string) => {
      const token = readAuthToken();

      if (!token) {
        clearAuthSession();
        onAuthRequired();
        return;
      }

      setSubscriptionActionState("loading");
      setSubscriptionActionMessage("Создаем платеж…");

      try {
        const checkout = await createCabinetSubscriptionCheckout(token, planCode);
        setSubscriptionActionState("success");
        setSubscriptionActionMessage("Перенаправляем на страницу оплаты…");
        window.location.assign(checkout.checkoutUrl);
      } catch {
        setSubscriptionActionState("error");
        setSubscriptionActionMessage("Не удалось создать платеж.");
      }
    },
    [onAuthRequired],
  );

  return {
    isRenewModalOpen,
    subscriptionActionMessage,
    subscriptionActionState,
    closeRenewModal,
    handleSubscriptionCheckout,
    openRenewModal,
  };
}
