"use client";

import { useState } from "react";

import type { CabinetTelegramLink } from "./cabinet-models";
import styles from "./cabinet-page.module.css";

type CabinetProfileModalProps = {
  isOpen: boolean;
  profile: {
    email: string;
    firstName: string;
    lastName: string;
    telegramHandle: string;
    currentPassword: string;
    newPassword: string;
  };
  saveState: "idle" | "loading" | "success" | "error";
  saveMessage: string;
  telegramLink: CabinetTelegramLink | null;
  telegramLinkActionState: "idle" | "loading" | "success" | "error";
  telegramLinkActionMessage: string;
  telegramLinkDeepLinkUrl: string | null;
  onClose: () => void;
  onSave: () => void;
  onCreateTelegramLink: () => void;
  onUnlinkTelegram: () => void;
  onChangeField: (
    field:
      | "email"
      | "firstName"
      | "lastName"
      | "telegramHandle"
      | "currentPassword"
      | "newPassword",
    value: string,
  ) => void;
};

function resolveLinkedTelegramLabel(telegramLink: CabinetTelegramLink | null) {
  if (!telegramLink?.isLinked) {
    return "Telegram не привязан";
  }

  if (telegramLink.telegramUsername) {
    return `@${telegramLink.telegramUsername.replace(/^@/, "")}`;
  }

  if (telegramLink.telegramFullName) {
    return telegramLink.telegramFullName;
  }

  return `ID ${telegramLink.telegramUserId}`;
}

function resolveLinkedTelegramMeta(telegramLink: CabinetTelegramLink | null) {
  if (!telegramLink?.isLinked) {
    return "Аккаунт Telegram пока не подключен.";
  }

  const identityParts = [];
  if (telegramLink.telegramUsername) {
    identityParts.push(`@${telegramLink.telegramUsername.replace(/^@/, "")}`);
  }
  if (telegramLink.telegramUserId) {
    identityParts.push(`ID ${telegramLink.telegramUserId}`);
  }

  if (identityParts.length > 0) {
    return identityParts.join(" · ");
  }

  return "Telegram успешно привязан.";
}

export function CabinetProfileModal({
  isOpen,
  profile,
  saveState,
  saveMessage,
  telegramLink,
  telegramLinkActionState,
  telegramLinkActionMessage,
  telegramLinkDeepLinkUrl,
  onClose,
  onSave,
  onCreateTelegramLink,
  onUnlinkTelegram,
  onChangeField,
}: CabinetProfileModalProps) {
  const [copyLabel, setCopyLabel] = useState("Скопировать ссылку");

  if (!isOpen) {
    return null;
  }

  return (
    <div
      className={styles.modalOverlay}
      role="presentation"
      onClick={onClose}
    >
      <div
        className={styles.modalCard}
        role="dialog"
        aria-modal="true"
        aria-labelledby="profile-modal-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className={styles.modalHead}>
          <div>
            <h2 id="profile-modal-title" className={styles.modalTitle}>
              Настройки профиля
            </h2>
            <p className={styles.modalText}>
              Почта, Telegram и пароль управляются из одного окна.
            </p>
          </div>
          <button
            type="button"
            className={styles.modalCloseButton}
            onClick={onClose}
          >
            Закрыть
          </button>
        </div>

        <div className={styles.settingsGrid}>
          <label className={styles.settingsField}>
            <span>Имя</span>
            <input
              className={styles.settingsInput}
              type="text"
              value={profile.firstName}
              onChange={(event) => onChangeField("firstName", event.target.value)}
            />
          </label>

          <label className={styles.settingsField}>
            <span>Фамилия</span>
            <input
              className={styles.settingsInput}
              type="text"
              value={profile.lastName}
              onChange={(event) => onChangeField("lastName", event.target.value)}
            />
          </label>

          <label className={styles.settingsField}>
            <span>Email</span>
            <input
              className={styles.settingsInput}
              type="email"
              value={profile.email}
              onChange={(event) => onChangeField("email", event.target.value)}
            />
          </label>

          <label className={styles.settingsField}>
            <span>Текущий пароль</span>
            <input
              className={styles.settingsInput}
              type="password"
              value={profile.currentPassword}
              onChange={(event) =>
                onChangeField("currentPassword", event.target.value)
              }
              placeholder="Введите текущий пароль"
            />
          </label>

          <label className={styles.settingsField}>
            <span>Новый пароль</span>
            <input
              className={styles.settingsInput}
              type="password"
              value={profile.newPassword}
              onChange={(event) => onChangeField("newPassword", event.target.value)}
              placeholder="Введите новый пароль"
            />
          </label>
        </div>

        <div className={styles.noticeCard}>
          <strong>Привязка Telegram</strong>
          <div className={styles.telegramStatusCard}>
            <div className={styles.telegramStatusHeader}>
              <div>
                <div className={styles.telegramIdentity}>
                  {resolveLinkedTelegramLabel(telegramLink)}
                </div>
                <div className={styles.telegramMeta}>
                  {resolveLinkedTelegramMeta(telegramLink)}
                </div>
              </div>
              <span
                className={`${styles.telegramStatusBadge} ${
                  telegramLink?.isLinked
                    ? styles.telegramStatusBadgeLinked
                    : styles.telegramStatusBadgePending
                }`}
              >
                {telegramLink?.isLinked ? "✓ Привязано" : "Не привязан"}
              </span>
            </div>
            {telegramLink?.linkedAt ? (
              <p>Подключено: {telegramLink.linkedAt}</p>
            ) : null}
          </div>
          {telegramLink?.pendingLinkExpiresAt ? (
            <p>Активная ссылка привязки действует до {telegramLink.pendingLinkExpiresAt}.</p>
          ) : null}
          {telegramLinkActionMessage ? (
            <p>{telegramLinkActionMessage}</p>
          ) : null}

          <div className={styles.telegramLinkActions}>
            {!telegramLink?.isLinked ? (
              <button
                type="button"
                data-testid="telegram-create-link-button"
                className={styles.primaryButton}
                disabled={telegramLinkActionState === "loading"}
                onClick={onCreateTelegramLink}
              >
                {telegramLinkActionState === "loading" ? "Открываем Telegram…" : "Привязать Telegram"}
              </button>
            ) : (
              <button
                type="button"
                className={styles.secondaryButton}
                disabled={telegramLinkActionState === "loading"}
                onClick={onUnlinkTelegram}
              >
                {telegramLinkActionState === "loading" ? "Обновляем…" : "Отвязать Telegram"}
              </button>
            )}

            {telegramLinkDeepLinkUrl ? (
              <>
                <a
                  className={styles.secondaryButton}
                  href={telegramLinkDeepLinkUrl}
                  target="_blank"
                  rel="noreferrer"
                >
                  Открыть бота еще раз
                </a>
                <button
                  type="button"
                  className={styles.secondaryButton}
                  onClick={async () => {
                    await navigator.clipboard.writeText(telegramLinkDeepLinkUrl);
                    setCopyLabel("Скопировано");
                    window.setTimeout(() => setCopyLabel("Скопировать ссылку"), 1400);
                  }}
                >
                  {copyLabel}
                </button>
              </>
            ) : null}
          </div>
        </div>

        <div
          className={`${styles.profileStatus} ${
            saveState !== "idle" ? styles.profileStatusVisible : ""
          } ${
            saveState === "loading" ? styles.profileStatusLoading : ""
          } ${
            saveState === "success"
              ? styles.profileStatusSuccess
              : saveState === "error"
                ? styles.profileStatusError
                : ""
          }`}
        >
          <span className={styles.profileStatusDot} aria-hidden="true" />
          <span>{saveMessage}</span>
        </div>

        <div className={styles.modalActions}>
          <button
            type="button"
            className={styles.secondaryButton}
            onClick={onClose}
          >
            Отмена
          </button>
          <button
            type="button"
            className={styles.primaryButton}
            disabled={saveState === "loading"}
            onClick={onSave}
          >
            {saveState === "loading" ? "Сохранение…" : "Сохранить"}
          </button>
        </div>
      </div>
    </div>
  );
}
