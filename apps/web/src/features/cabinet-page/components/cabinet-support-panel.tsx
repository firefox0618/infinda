"use client";

import { useId } from "react";

import styles from "./cabinet-page.module.css";

import { AttachIcon, SupportPulseIcon } from "./cabinet-icons";

type CabinetMessage = {
  id: string;
  author: string;
  side: "support" | "user";
  text: string;
  attachments?: readonly string[];
};

type CabinetSupportPanelProps = {
  attachedFiles: readonly string[];
  message: string;
  messages: readonly CabinetMessage[];
  onChangeMessage: (value: string) => void;
  onChangeFiles: (files: FileList | null) => void;
  onRemoveFile: (fileName: string) => void;
  onSendMessage: () => void;
};

export function CabinetSupportPanel({
  attachedFiles,
  message,
  messages,
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
          <div className={styles.panelSub}>Чат по настройке, доступу и устройствам</div>
        </div>
        <span className={styles.supportHeaderIcon} aria-hidden="true">
          <SupportPulseIcon />
        </span>
      </div>

      <div className={styles.supportPanelBody}>
        <div className={styles.chatMessages}>
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
                    <span key={attachment} className={styles.messageAttachmentChip}>
                      {attachment}
                    </span>
                  ))}
                </div>
              ) : null}
            </div>
          ))}
        </div>

        <div className={styles.chatComposer}>
          {attachedFiles.length ? (
            <div className={styles.pendingFiles}>
              {attachedFiles.map((fileName) => (
                <button
                  key={fileName}
                  type="button"
                  className={styles.pendingFileChip}
                  onClick={() => onRemoveFile(fileName)}
                >
                  <span>{fileName}</span>
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
              className={styles.chatInput}
              type="text"
              value={message}
              onChange={(event) => onChangeMessage(event.target.value)}
              placeholder="Напишите сообщение..."
            />
            <label htmlFor={fileInputId} className={styles.attachButton}>
              <AttachIcon />
              <span>Файл</span>
            </label>
            <button
              type="button"
              className={styles.primaryButton}
              onClick={onSendMessage}
            >
              Отправить
            </button>
          </div>
        </div>
      </div>
    </article>
  );
}
