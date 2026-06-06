"use client";

import { useCallback, useState } from "react";

import { cabinetMessages } from "../data/cabinet-content";
import type { CabinetMessage } from "../components/cabinet-models";

export function useCabinetSupportState() {
  const [messages, setMessages] = useState<CabinetMessage[]>([...cabinetMessages]);
  const [messageDraft, setMessageDraft] = useState("");
  const [attachedFiles, setAttachedFiles] = useState<string[]>([]);

  const handleSendMessage = useCallback(() => {
    const value = messageDraft.trim();

    if (!value && attachedFiles.length === 0) {
      return;
    }

    setMessages((current) => [
      ...current,
      {
        id: `user-${Date.now()}`,
        author: "Вы",
        side: "user",
        text: value || "Прикреплены файлы",
        attachments: attachedFiles.length ? attachedFiles : undefined,
      },
    ]);
    setMessageDraft("");
    setAttachedFiles([]);
  }, [attachedFiles, messageDraft]);

  return {
    messages,
    messageDraft,
    attachedFiles,
    setMessageDraft,
    setAttachedFiles,
    handleSendMessage,
  };
}
