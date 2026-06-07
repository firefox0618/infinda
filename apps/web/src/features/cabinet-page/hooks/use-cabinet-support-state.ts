"use client";

import { useCallback, useEffect, useState } from "react";

import { clearAuthSession, readAuthToken } from "@/shared/auth/auth-storage";
import {
  CabinetRequestError,
  fetchCabinetSupportConversation,
  sendCabinetSupportMessage,
} from "../api/cabinet-client";
import type { CabinetSupportConversation } from "../components/cabinet-models";

type UseCabinetSupportStateArgs = {
  onAuthRequired: () => void;
};

type SupportLoadState = "idle" | "loading" | "ready" | "error";
type SupportSendState = "idle" | "sending" | "error";

export function useCabinetSupportState({
  onAuthRequired,
}: UseCabinetSupportStateArgs) {
  const [conversation, setConversation] = useState<CabinetSupportConversation | null>(null);
  const [messageDraft, setMessageDraft] = useState("");
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);
  const [loadState, setLoadState] = useState<SupportLoadState>("loading");
  const [sendState, setSendState] = useState<SupportSendState>("idle");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const token = readAuthToken();

    if (!token) {
      clearAuthSession();
      onAuthRequired();
      return;
    }

    let isCancelled = false;

    void fetchCabinetSupportConversation(token)
      .then((nextConversation) => {
        if (isCancelled) {
          return;
        }

        setConversation(nextConversation);
        setLoadState("ready");
        setErrorMessage("");
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
          return;
        }

        setLoadState("error");
        setErrorMessage(
          error instanceof Error
            ? error.message
            : "Не удалось загрузить диалог поддержки.",
        );
      });

    return () => {
      isCancelled = true;
    };
  }, [onAuthRequired]);

  const handleSendMessage = useCallback(async () => {
    const token = readAuthToken();

    if (!token) {
      clearAuthSession();
      onAuthRequired();
      return;
    }

    const value = messageDraft.trim();

    if (!value && attachedFiles.length === 0) {
      return;
    }

    setSendState("sending");
    setErrorMessage("");

    try {
      const nextConversation = await sendCabinetSupportMessage(token, {
        text: value,
        files: attachedFiles,
      });
      setConversation(nextConversation);
      setMessageDraft("");
      setAttachedFiles([]);
      setSendState("idle");
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

      setSendState("error");
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Не удалось отправить сообщение в поддержку.",
      );
    }
  }, [attachedFiles, messageDraft, onAuthRequired]);

  const handleChangeFiles = useCallback((files: FileList | null) => {
    setAttachedFiles(files ? Array.from(files) : []);
  }, []);

  const handleRemoveFile = useCallback((fileName: string) => {
    setAttachedFiles((current) => current.filter((file) => file.name !== fileName));
  }, []);

  return {
    attachedFiles,
    conversation,
    errorMessage,
    loadState,
    messageDraft,
    messages: conversation?.messages ?? [],
    sendState,
    setMessageDraft,
    handleChangeFiles,
    handleRemoveFile,
    handleSendMessage,
  };
}
