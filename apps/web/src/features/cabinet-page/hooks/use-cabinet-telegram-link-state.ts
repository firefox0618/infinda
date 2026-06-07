"use client";

import { useCallback, useEffect, useState } from "react";

import { clearAuthSession, readAuthToken } from "@/shared/auth/auth-storage";
import {
  CabinetRequestError,
  createCabinetTelegramLinkToken,
  fetchCabinetTelegramLinkStatus,
  unlinkCabinetTelegram,
} from "../api/cabinet-client";
import type { CabinetTelegramLink } from "../components/cabinet-models";

type TelegramActionState = "idle" | "loading" | "success" | "error";

type UseCabinetTelegramLinkStateArgs = {
  onAuthRequired: () => void;
};

export function useCabinetTelegramLinkState({
  onAuthRequired,
}: UseCabinetTelegramLinkStateArgs) {
  const [telegramLink, setTelegramLink] = useState<CabinetTelegramLink | null>(null);
  const [linkActionState, setLinkActionState] = useState<TelegramActionState>("idle");
  const [linkActionMessage, setLinkActionMessage] = useState("");
  const [deepLinkUrl, setDeepLinkUrl] = useState<string | null>(null);

  const loadTelegramLinkStatus = useCallback(async () => {
    const token = readAuthToken();

    if (!token) {
      clearAuthSession();
      onAuthRequired();
      return;
    }

    try {
      const nextStatus = await fetchCabinetTelegramLinkStatus(token);
      setTelegramLink(nextStatus);
      setDeepLinkUrl(nextStatus.pendingDeepLinkUrl);
    } catch (error) {
      if (
        error instanceof CabinetRequestError &&
        (error.errorCode === "AUTHENTICATION_FAILED" ||
          error.errorCode === "NOT_AUTHENTICATED")
      ) {
        clearAuthSession();
        onAuthRequired();
      }
    }
  }, [onAuthRequired]);

  useEffect(() => {
    const token = readAuthToken();

    if (!token) {
      clearAuthSession();
      onAuthRequired();
      return;
    }

    let isCancelled = false;

    void fetchCabinetTelegramLinkStatus(token)
      .then((nextStatus) => {
        if (isCancelled) {
          return;
        }

        setTelegramLink(nextStatus);
        setDeepLinkUrl(nextStatus.pendingDeepLinkUrl);
      })
      .catch((error) => {
        if (isCancelled) {
          return;
        }

        if (
          error instanceof CabinetRequestError &&
          (error.errorCode === "AUTHENTICATION_FAILED" ||
            error.errorCode === "NOT_AUTHENTICATED")
        ) {
          clearAuthSession();
          onAuthRequired();
        }
      });

    return () => {
      isCancelled = true;
    };
  }, [onAuthRequired]);

  useEffect(() => {
    if (!telegramLink?.pendingLinkExpiresAt || telegramLink.isLinked) {
      return;
    }

    const intervalId = window.setInterval(() => {
      void loadTelegramLinkStatus();
    }, 5000);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [loadTelegramLinkStatus, telegramLink?.isLinked, telegramLink?.pendingLinkExpiresAt]);

  const handleCreateLink = useCallback(async () => {
    const token = readAuthToken();

    if (!token) {
      clearAuthSession();
      onAuthRequired();
      return;
    }

    setLinkActionState("loading");
    setLinkActionMessage("Готовим ссылку привязки…");

    try {
      const nextLink = await createCabinetTelegramLinkToken(token);
      await loadTelegramLinkStatus();
      setDeepLinkUrl(nextLink.deepLinkUrl);
      setLinkActionState("success");
      setLinkActionMessage("Открываем Telegram для привязки аккаунта…");
      window.location.assign(nextLink.deepLinkUrl);
    } catch (error) {
      if (
        error instanceof CabinetRequestError &&
        (error.errorCode === "AUTHENTICATION_FAILED" ||
          error.errorCode === "NOT_AUTHENTICATED")
      ) {
        clearAuthSession();
        onAuthRequired();
        return;
      }

      setLinkActionState("error");
      setLinkActionMessage(
        error instanceof Error
          ? error.message
          : "Не удалось создать ссылку привязки Telegram.",
      );
    }
  }, [loadTelegramLinkStatus, onAuthRequired]);

  const handleUnlink = useCallback(async () => {
    const token = readAuthToken();

    if (!token) {
      clearAuthSession();
      onAuthRequired();
      return;
    }

    setLinkActionState("loading");
    setLinkActionMessage("Отвязываем Telegram…");

    try {
      const nextStatus = await unlinkCabinetTelegram(token);
      setTelegramLink(nextStatus);
      setDeepLinkUrl(nextStatus.pendingDeepLinkUrl);
      setLinkActionState("success");
      setLinkActionMessage("Telegram отвязан от аккаунта.");
    } catch (error) {
      if (
        error instanceof CabinetRequestError &&
        (error.errorCode === "AUTHENTICATION_FAILED" ||
          error.errorCode === "NOT_AUTHENTICATED")
      ) {
        clearAuthSession();
        onAuthRequired();
        return;
      }

      setLinkActionState("error");
      setLinkActionMessage(
        error instanceof Error
          ? error.message
          : "Не удалось отвязать Telegram.",
      );
    }
  }, [onAuthRequired]);

  return {
    deepLinkUrl,
    linkActionMessage,
    linkActionState,
    telegramLink,
    handleCreateLink,
    handleUnlink,
    loadTelegramLinkStatus,
  };
}
