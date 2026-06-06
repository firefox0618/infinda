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
  onClose: () => void;
  onSave: () => void;
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

export function CabinetProfileModal({
  isOpen,
  profile,
  saveState,
  saveMessage,
  onClose,
  onSave,
  onChangeField,
}: CabinetProfileModalProps) {
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
            <span>Telegram</span>
            <input
              className={styles.settingsInput}
              type="text"
              value={profile.telegramHandle}
              onChange={(event) =>
                onChangeField("telegramHandle", event.target.value)
              }
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
