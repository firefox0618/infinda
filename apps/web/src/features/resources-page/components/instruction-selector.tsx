"use client";

import Link from "next/link";
import { useState } from "react";

import type { ResourcesIconName } from "./resources-icon";
import styles from "./resources-page.module.css";

import { ResourcesIcon } from "./resources-icon";

type SelectorItem = {
  label: string;
  icon: ResourcesIconName;
};

type InstructionSelectorProps = {
  clients: readonly SelectorItem[];
  platforms: readonly SelectorItem[];
};

export function InstructionSelector({
  clients,
  platforms,
}: InstructionSelectorProps) {
  const [activeClient, setActiveClient] = useState(clients[0]?.label ?? "");
  const [activePlatform, setActivePlatform] = useState(
    platforms[0]?.label ?? "",
  );
  const instructionKey = `${activeClient}-${activePlatform}`
    .toLowerCase()
    .replace(/\s+/g, "-");

  return (
    <div className={styles.instructionsLayout}>
      <div className={styles.selectorGroup}>
        <div className={styles.selectorLabel}>Выберите клиент</div>
        <div className={styles.selectorGrid}>
          {clients.map((item) => (
            <button
              key={item.label}
              type="button"
              className={`${styles.selectorButton} ${
                activeClient === item.label ? styles.selectorButtonActive : ""
              }`}
              onClick={() => setActiveClient(item.label)}
            >
              <span className={styles.instructionIcon}>
                <ResourcesIcon name={item.icon} />
              </span>
              <span className={styles.instructionLabel}>{item.label}</span>
            </button>
          ))}
        </div>
      </div>

      <div className={styles.selectorGroup}>
        <div className={styles.selectorLabel}>Выберите платформу</div>
        <div className={styles.selectorGrid}>
          {platforms.map((item) => (
            <button
              key={item.label}
              type="button"
              className={`${styles.selectorButton} ${
                activePlatform === item.label ? styles.selectorButtonActive : ""
              }`}
              onClick={() => setActivePlatform(item.label)}
            >
              <span className={styles.instructionIcon}>
                <ResourcesIcon name={item.icon} />
              </span>
              <span className={styles.instructionLabel}>{item.label}</span>
            </button>
          ))}
        </div>
      </div>

      <Link
        href={`#instruction-preview-${instructionKey}`}
        className={styles.instructionActionButton}
      >
        Выбран сценарий: {activeClient} для {activePlatform}
      </Link>
    </div>
  );
}
