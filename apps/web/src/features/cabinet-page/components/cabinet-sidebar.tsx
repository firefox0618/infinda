"use client";

import type { AuthUser } from "@/shared/auth/auth-types";

import styles from "./cabinet-page.module.css";

import { CabinetNavIcon, LogoutIcon } from "./cabinet-icons";
import type { CabinetTab } from "./cabinet-models";

const cabinetTabs: { id: CabinetTab; label: string; note: string }[] = [
  { id: "overview", label: "Обзор", note: "общая картина" },
  { id: "subscription", label: "Подписка", note: "ссылки и статус" },
  { id: "devices", label: "Устройства", note: "контроль доступа" },
  { id: "support", label: "Поддержка", note: "чат и помощь" },
];

type CabinetSidebarProps = {
  activeTab: CabinetTab;
  currentUser: AuthUser | null;
  isCompact: boolean;
  isMobileOpen: boolean;
  onToggleCompact: () => void;
  onCloseMobile: () => void;
  onOpenProfile: () => void;
  onLogout: () => void;
  onSelectTab: (tab: CabinetTab) => void;
};

export function CabinetSidebar({
  activeTab,
  currentUser,
  isCompact,
  isMobileOpen,
  onToggleCompact,
  onCloseMobile,
  onOpenProfile,
  onLogout,
  onSelectTab,
}: CabinetSidebarProps) {
  const userDisplayName =
    [currentUser?.first_name, currentUser?.last_name].filter(Boolean).join(" ") ||
    currentUser?.username ||
    "Пользователь";
  const avatarLetter = userDisplayName.charAt(0).toUpperCase() || "U";

  return (
    <>
      <div
        className={`${styles.mobileOverlay} ${
          isMobileOpen ? styles.mobileOverlayVisible : ""
        }`}
        aria-hidden="true"
        onClick={onCloseMobile}
      />

      <aside
        className={`${styles.sidebar} ${
          isCompact ? styles.sidebarCompact : ""
        } ${isMobileOpen ? styles.sidebarMobileOpen : ""}`}
      >
        <div className={styles.sidebarHead}>
          <div className={styles.sidebarBrand}>
            <span className={styles.sidebarBrandMark} aria-hidden="true" />
            <div className={styles.sidebarBrandText}>
              <strong>INFINDA</strong>
              <span>кабинет</span>
            </div>
          </div>

          <button
            type="button"
            className={styles.sidebarToggle}
            aria-label={isCompact ? "Развернуть меню" : "Свернуть меню"}
            onClick={onToggleCompact}
          >
            <span />
            <span />
          </button>
        </div>

        <div className={styles.sidebarSectionLabel}>Навигация</div>

        <nav className={styles.sidebarNav} aria-label="Разделы кабинета">
          {cabinetTabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              className={`${styles.sidebarButton} ${
                activeTab === tab.id ? styles.sidebarButtonActive : ""
              }`}
              data-tooltip={tab.label}
              onClick={() => {
                onSelectTab(tab.id);
                onCloseMobile();
              }}
            >
              <span className={styles.sidebarButtonIcon} aria-hidden="true">
                <CabinetNavIcon tab={tab.id} />
              </span>
              <span className={styles.sidebarButtonCopy}>
                <span className={styles.sidebarButtonLabel}>{tab.label}</span>
                <span className={styles.sidebarButtonNote}>{tab.note}</span>
              </span>
            </button>
          ))}
        </nav>

        <div className={styles.sidebarFooter}>
          <button
            type="button"
            className={styles.userCard}
            onClick={onOpenProfile}
            aria-label="Открыть настройки профиля"
            data-tooltip="Профиль"
          >
            <div className={styles.userAvatar}>{avatarLetter}</div>
            <div className={styles.userMeta}>
              <div className={styles.userName}>{userDisplayName}</div>
              <div className={styles.userEmail}>
                {currentUser?.email ?? "email не указан"}
              </div>
            </div>
          </button>

          <button
            type="button"
            className={styles.logoutButton}
            aria-label="Выйти"
            data-tooltip="Выйти"
            onClick={onLogout}
          >
            <LogoutIcon />
            <span className={styles.logoutLabel}>Выйти</span>
          </button>
        </div>
      </aside>
    </>
  );
}
