"use client";

import { useState } from "react";

import styles from "./about-page.module.css";

type ContactCopyButtonProps = {
  value: string;
};

export function ContactCopyButton({ value }: ContactCopyButtonProps) {
  const [isCopied, setIsCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      setIsCopied(true);
      window.setTimeout(() => setIsCopied(false), 1800);
    } catch {
      setIsCopied(false);
    }
  };

  return (
    <button type="button" className={styles.copyButton} onClick={handleCopy}>
      {isCopied ? "Скопировано" : "Скопировать"}
    </button>
  );
}
