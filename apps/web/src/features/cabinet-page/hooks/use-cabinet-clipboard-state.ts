"use client";

import { useCallback, useState } from "react";

type CopyScope = "main" | "server";

export function useCabinetClipboardState() {
  const [mainCopyLabel, setMainCopyLabel] = useState("Скопировать ссылку");
  const [serverCopyLabel, setServerCopyLabel] = useState("Скопировать маршрут");

  const writeToClipboard = useCallback(async (value: string, scope: CopyScope) => {
    try {
      await navigator.clipboard.writeText(value);

      if (scope === "main") {
        setMainCopyLabel("Ссылка скопирована");
        window.setTimeout(() => setMainCopyLabel("Скопировать ссылку"), 1800);
      } else {
        setServerCopyLabel("Маршрут скопирован");
        window.setTimeout(() => setServerCopyLabel("Скопировать маршрут"), 1800);
      }
    } catch {
      if (scope === "main") {
        setMainCopyLabel("Не удалось скопировать");
        window.setTimeout(() => setMainCopyLabel("Скопировать ссылку"), 1800);
      } else {
        setServerCopyLabel("Не удалось скопировать");
        window.setTimeout(() => setServerCopyLabel("Скопировать маршрут"), 1800);
      }
    }
  }, []);

  return {
    mainCopyLabel,
    serverCopyLabel,
    writeToClipboard,
  };
}
