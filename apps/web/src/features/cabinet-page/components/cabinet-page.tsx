"use client";

import { useMemo, useState } from "react";

import styles from "./cabinet-page.module.css";

import { CabinetDevicesPanel } from "./cabinet-devices-panel";
import { CabinetOverviewPanel } from "./cabinet-overview-panel";
import { CabinetSidebar } from "./cabinet-sidebar";
import { CabinetSubscriptionPanel } from "./cabinet-subscription-panel";
import { CabinetSupportPanel } from "./cabinet-support-panel";
import type { CabinetTab } from "./cabinet-types";
import {
  cabinetDevices,
  cabinetMessages,
  cabinetOverviewStats,
  cabinetSubscriptionDetails,
  cabinetSubscriptionLinks,
} from "../data/cabinet-content";

type CountryCode = (typeof cabinetSubscriptionLinks.countries)[number]["code"];

type CabinetDevice = {
  name: string;
  icon: "desktop" | "mobile" | "laptop";
  ip: string;
  lastSeen: string;
  status: "online" | "offline";
  meta: string;
};

type CabinetMessage = {
  id: string;
  author: string;
  side: "support" | "user";
  text: string;
  attachments?: readonly string[];
};

export function CabinetPage() {
  const [activeTab, setActiveTab] = useState<CabinetTab>("overview");
  const [isSidebarCompact, setIsSidebarCompact] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [isRenewModalOpen, setIsRenewModalOpen] = useState(false);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [selectedCountry, setSelectedCountry] = useState<CountryCode>(
    cabinetSubscriptionLinks.countries[0].code,
  );
  const [devices, setDevices] = useState<CabinetDevice[]>([...cabinetDevices]);
  const [messages, setMessages] = useState<CabinetMessage[]>([
    ...cabinetMessages,
  ]);
  const [messageDraft, setMessageDraft] = useState("");
  const [attachedFiles, setAttachedFiles] = useState<string[]>([]);
  const [mainCopyLabel, setMainCopyLabel] = useState("Скопировать ссылку");
  const [serverCopyLabel, setServerCopyLabel] = useState("Скопировать маршрут");
  const [profileEmail, setProfileEmail] = useState("alexey@infinda.com");
  const [profileTelegram, setProfileTelegram] = useState("@alexey_infinda");
  const [profilePassword, setProfilePassword] = useState("");

  const currentSection = useMemo(() => {
    if (activeTab === "overview") {
      return { title: "Обзор", subtitle: "Текущая активность и доступ" };
    }

    if (activeTab === "subscription") {
      return { title: "Подписка", subtitle: "Ссылки, параметры и маршруты" };
    }

    if (activeTab === "devices") {
      return { title: "Устройства", subtitle: "Контроль подключений и активности" };
    }

    return { title: "Поддержка", subtitle: "Чат и быстрые решения" };
  }, [activeTab]);

  const selectedCountryLink = useMemo(
    () =>
      cabinetSubscriptionLinks.countries.find(
        (country) => country.code === selectedCountry,
      ) ?? cabinetSubscriptionLinks.countries[0],
    [selectedCountry],
  );

  const writeToClipboard = async (value: string, scope: "main" | "server") => {
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
  };

  const handleSendMessage = () => {
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
  };

  return (
    <div className={styles.page}>
      <div className={styles.background} aria-hidden="true" />

      <div className={styles.container}>
        <section className={styles.workspace}>
          <CabinetSidebar
            activeTab={activeTab}
            isCompact={isSidebarCompact}
            isMobileOpen={isMobileSidebarOpen}
            onToggleCompact={() => {
              if (typeof window !== "undefined" && window.innerWidth <= 980) {
                setIsMobileSidebarOpen((current) => !current);
                return;
              }

              setIsSidebarCompact((current) => !current);
            }}
            onCloseMobile={() => setIsMobileSidebarOpen(false)}
            onOpenProfile={() => setIsProfileModalOpen(true)}
            onSelectTab={setActiveTab}
          />

          <div className={styles.content}>
            <section className={styles.pageTop}>
              <div className={styles.pageTitle}>
                <span className={styles.statusDot} aria-hidden="true" />
                <div>
                  <h1>{currentSection.title}</h1>
                  <p>{currentSection.subtitle}</p>
                </div>
              </div>

              <div className={styles.pageActions}>
                <button
                  type="button"
                  className={styles.topButton}
                  onClick={() => setActiveTab("support")}
                >
                  Поддержка
                </button>
                <button
                  type="button"
                  className={`${styles.topButton} ${styles.topButtonPrimary}`}
                  onClick={() => setIsRenewModalOpen(true)}
                >
                  Продлить
                </button>
                <button
                  type="button"
                  className={styles.mobileMenuButton}
                  onClick={() => setIsMobileSidebarOpen(true)}
                >
                  Меню
                </button>
              </div>
            </section>

            {activeTab === "overview" ? (
              <CabinetOverviewPanel
                stats={cabinetOverviewStats}
                mainLink={cabinetSubscriptionLinks.main}
                devices={devices}
                copyLabel={mainCopyLabel}
                onCopyMainLink={() =>
                  void writeToClipboard(cabinetSubscriptionLinks.main, "main")
                }
                onOpenTab={setActiveTab}
              />
            ) : null}

            {activeTab === "subscription" ? (
              <CabinetSubscriptionPanel
                mainLink={cabinetSubscriptionLinks.main}
                countries={cabinetSubscriptionLinks.countries}
                selectedCountryCode={selectedCountry}
                selectedCountryUrl={selectedCountryLink.url}
                details={cabinetSubscriptionDetails}
                mainCopyLabel={mainCopyLabel}
                serverCopyLabel={serverCopyLabel}
                onSelectCountry={(countryCode) =>
                  setSelectedCountry(countryCode as CountryCode)
                }
                onCopyMainLink={() =>
                  void writeToClipboard(cabinetSubscriptionLinks.main, "main")
                }
                onCopyCountryLink={() =>
                  void writeToClipboard(selectedCountryLink.url, "server")
                }
              />
            ) : null}

            {activeTab === "devices" ? (
              <CabinetDevicesPanel
                devices={devices}
                onRevokeDevice={(deviceName) =>
                  setDevices((current) =>
                    current.filter((device) => device.name !== deviceName),
                  )
                }
              />
            ) : null}

            {activeTab === "support" ? (
              <CabinetSupportPanel
                attachedFiles={attachedFiles}
                message={messageDraft}
                messages={messages}
                onChangeMessage={setMessageDraft}
                onChangeFiles={(files) =>
                  setAttachedFiles(
                    files ? Array.from(files, (file) => file.name) : [],
                  )
                }
                onRemoveFile={(fileName) =>
                  setAttachedFiles((current) =>
                    current.filter((name) => name !== fileName),
                  )
                }
                onSendMessage={handleSendMessage}
              />
            ) : null}
          </div>
        </section>
      </div>

      {isRenewModalOpen ? (
        <div
          className={styles.modalOverlay}
          role="presentation"
          onClick={() => setIsRenewModalOpen(false)}
        >
          <div
            className={styles.modalCard}
            role="dialog"
            aria-modal="true"
            aria-labelledby="renew-modal-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className={styles.modalHead}>
              <div>
                <h2 id="renew-modal-title" className={styles.modalTitle}>
                  Продлить подписку
                </h2>
                <p className={styles.modalText}>
                  Выберите срок и перейдите к оплате в следующем шаге.
                </p>
              </div>
              <button
                type="button"
                className={styles.modalCloseButton}
                onClick={() => setIsRenewModalOpen(false)}
              >
                Закрыть
              </button>
            </div>

            <div className={styles.tariffGrid}>
              {[
                { title: "1 месяц", price: "149 ₽", note: "Быстрый старт" },
                { title: "3 месяца", price: "399 ₽", note: "Оптимальный вариант" },
                { title: "6 месяцев", price: "749 ₽", note: "Выгоднее на длинный срок" },
                { title: "12 месяцев", price: "1290 ₽", note: "Максимальный доступ" },
              ].map((tariff) => (
                <article key={tariff.title} className={styles.tariffCard}>
                  <div className={styles.tariffTitle}>{tariff.title}</div>
                  <div className={styles.tariffPrice}>{tariff.price}</div>
                  <div className={styles.tariffNote}>{tariff.note}</div>
                  <button type="button" className={styles.primaryButton}>
                    Выбрать и оплатить
                  </button>
                </article>
              ))}
            </div>
          </div>
        </div>
      ) : null}

      {isProfileModalOpen ? (
        <div
          className={styles.modalOverlay}
          role="presentation"
          onClick={() => setIsProfileModalOpen(false)}
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
                onClick={() => setIsProfileModalOpen(false)}
              >
                Закрыть
              </button>
            </div>

            <div className={styles.settingsGrid}>
              <label className={styles.settingsField}>
                <span>Email</span>
                <input
                  className={styles.settingsInput}
                  type="email"
                  value={profileEmail}
                  onChange={(event) => setProfileEmail(event.target.value)}
                />
              </label>

              <label className={styles.settingsField}>
                <span>Telegram</span>
                <input
                  className={styles.settingsInput}
                  type="text"
                  value={profileTelegram}
                  onChange={(event) => setProfileTelegram(event.target.value)}
                />
              </label>

              <label className={styles.settingsField}>
                <span>Новый пароль</span>
                <input
                  className={styles.settingsInput}
                  type="password"
                  value={profilePassword}
                  onChange={(event) => setProfilePassword(event.target.value)}
                  placeholder="Введите новый пароль"
                />
              </label>
            </div>

            <div className={styles.modalActions}>
              <button
                type="button"
                className={styles.secondaryButton}
                onClick={() => setIsProfileModalOpen(false)}
              >
                Отмена
              </button>
              <button
                type="button"
                className={styles.primaryButton}
                onClick={() => {
                  setProfilePassword("");
                  setIsProfileModalOpen(false);
                }}
              >
                Сохранить
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
