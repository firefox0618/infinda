"use client";

import { useId } from "react";

import styles from "./cabinet-page.module.css";
import type {
  CabinetMessage,
  CabinetSupportConversationStatus,
} from "./cabinet-models";

import { AttachIcon, SupportPulseIcon } from "./cabinet-icons";

type CabinetSupportPanelProps = {
  assignedAdminName: string | null;
  attachedFiles: readonly File[];
  errorMessage: string;
  loadState: "idle" | "loading" | "ready" | "error";
  message: string;
  messages: readonly CabinetMessage[];
  sendState: "idle" | "sending" | "error";
  status: CabinetSupportConversationStatus | null;
  onChangeMessage: (value: string) => void;
  onChangeFiles: (files: FileList | null) => void;
  onRemoveFile: (fileName: string) => void;
  onSendMessage: () => void;
};

function getConversationStatusLabel(status: CabinetSupportConversationStatus | null) {
  if (status === "closed") {
    return "Диалог закрыт";
  }

  if (status === "in_progress") {
    return "Диалог в работе";
  }

  return "Новое обращение";
}

export function CabinetSupportPanel({
  assignedAdminName,
  attachedFiles,
  errorMessage,
  loadState,
  message,
  messages,
  sendState,
  status,
  onChangeMessage,
  onChangeFiles,
  onRemoveFile,
  onSendMessage,
}: CabinetSupportPanelProps) {
  const fileInputId = useId();

  return (
    <article className={styles.supportPanel}>
      <div className={styles.panelHead}>
        <div>
          <div className={styles.panelTitle}>Поддержка онлайн</div>
          <div className={styles.panelSub}>
            {getConversationStatusLabel(status)}
            {assignedAdminName ? ` · ведет ${assignedAdminName}` : ""}
          </div>
        </div>
        <span className={styles.supportHeaderIcon} aria-hidden="true">
          <SupportPulseIcon />
        </span>
      </div>

      <div className={styles.supportPanelBody}>
        <div className={styles.chatMessages}>
          {loadState === "loading" ? (
            <div className={styles.message}>
              <div className={styles.messageAuthor}>Система</div>
              <div>Загружаем историю диалога…</div>
            </div>
          ) : null}

          {loadState === "error" ? (
            <div className={styles.message}>
              <div className={styles.messageAuthor}>Система</div>
              <div>{errorMessage || "Не удалось загрузить поддержку."}</div>
            </div>
          ) : null}

          {loadState === "ready" && messages.length === 0 ? (
            <div className={styles.message}>
              <div className={styles.messageAuthor}>Поддержка</div>
              <div>Опишите вопрос по доступу, устройствам или настройке. Вся история сохранится в этом диалоге.</div>
            </div>
          ) : null}

          {messages.map((entry) => (
            <div
              key={entry.id}
              className={`${styles.message} ${
                entry.side === "user" ? styles.messageUser : styles.messageSupport
              }`}
            >
              <div className={styles.messageAuthor}>{entry.author}</div>
              <div>{entry.text}</div>
              {entry.attachments?.length ? (
                <div className={styles.messageAttachments}>
                  {entry.attachments.map((attachment) => (
                    <a
                      key={attachment.id}
                      className={styles.messageAttachmentChip}
                      href={attachment.url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {attachment.name}
                    </a>
                  ))}
                </div>
              ) : null}
              <div className={styles.messageMeta}>{entry.createdAt}</div>
            </div>
          ))}
        </div>

        <div className={styles.chatComposer}>
          {attachedFiles.length ? (
            <div className={styles.pendingFiles}>
              {attachedFiles.map((file) => (
                <button
                  key={file.name}
                  type="button"
                  className={styles.pendingFileChip}
                  onClick={() => onRemoveFile(file.name)}
                >
                  <span>{file.name}</span>
                  <span aria-hidden="true">×</span>
                </button>
              ))}
            </div>
          ) : null}

          <input
            id={fileInputId}
            className={styles.fileInput}
            type="file"
            multiple
            onChange={(event) => onChangeFiles(event.target.files)}
          />

          <div className={styles.chatComposerRow}>
            <input
              data-testid="support-message-input"
              className={styles.chatInput}
              type="text"
              value={message}
              onChange={(event) => onChangeMessage(event.target.value)}
              placeholder="Напишите сообщение..."
              disabled={loadState !== "ready" || sendState === "sending"}
            />
            <label htmlFor={fileInputId} className={styles.attachButton}>
              <AttachIcon />
              <span>Файл</span>
            </label>
            <button
              type="button"
              data-testid="support-send-button"
              className={styles.primaryButton}
              onClick={onSendMessage}
              disabled={loadState !== "ready" || sendState === "sending"}
            >
              {sendState === "sending" ? "Отправка…" : "Отправить"}
            </button>
          </div>

          {sendState === "error" && errorMessage ? (
            <div className={styles.messageMeta}>{errorMessage}</div>
          ) : null}
        </div>
      </div>
    </article>
  );
}
