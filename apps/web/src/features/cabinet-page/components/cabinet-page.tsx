"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import {
  AuthRequestError,
  fetchCurrentUser,
  logoutCurrentUser,
} from "@/shared/auth/auth-client";
import { navigateToErrorPage } from "@/shared/navigation/error-page-navigation";
import {
  clearAuthSession,
  readAuthToken,
  readStoredAuthUser,
  replaceStoredAuthUser,
} from "@/shared/auth/auth-storage";
import type { AuthUser } from "@/shared/auth/auth-types";

import styles from "./cabinet-page.module.css";
import {
  fetchCabinetDevices,
  fetchCabinetProfile,
  fetchCabinetSubscriptionPlans,
  fetchCabinetSubscription,
  createCabinetSubscriptionCheckout,
  revokeCabinetDevice,
  updateCabinetProfile,
  type CabinetSubscriptionPlan,
} from "../api/cabinet-client";

import { CabinetDevicesPanel } from "./cabinet-devices-panel";
import { CabinetOverviewPanel } from "./cabinet-overview-panel";
import { CabinetSidebar } from "./cabinet-sidebar";
import { CabinetSubscriptionPanel } from "./cabinet-subscription-panel";
import { CabinetSupportPanel } from "./cabinet-support-panel";
import {
  cabinetMessages,
  cabinetOverviewStats,
} from "../data/cabinet-content";
import type {
  CabinetDevice,
  CabinetMessage,
  CabinetOverviewStat,
  CabinetSubscription,
  CabinetTab,
} from "./cabinet-models";

const mobileCabinetTabs: { id: CabinetTab; label: string }[] = [
  { id: "overview", label: "Обзор" },
  { id: "subscription", label: "Подписка" },
  { id: "devices", label: "Устройства" },
  { id: "support", label: "Поддержка" },
];

export function CabinetPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<CabinetTab>("overview");
  const [isSidebarCompact, setIsSidebarCompact] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [isRenewModalOpen, setIsRenewModalOpen] = useState(false);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [selectedCountry, setSelectedCountry] = useState("");
  const [devices, setDevices] = useState<CabinetDevice[]>([]);
  const [subscription, setSubscription] = useState<CabinetSubscription | null>(null);
  const [messages, setMessages] = useState<CabinetMessage[]>([
    ...cabinetMessages,
  ]);
  const [messageDraft, setMessageDraft] = useState("");
  const [attachedFiles, setAttachedFiles] = useState<string[]>([]);
  const [mainCopyLabel, setMainCopyLabel] = useState("Скопировать ссылку");
  const [serverCopyLabel, setServerCopyLabel] = useState("Скопировать маршрут");
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(readStoredAuthUser());
  const [isSessionResolved, setIsSessionResolved] = useState(false);
  const [profileEmail, setProfileEmail] = useState(
    readStoredAuthUser()?.email ?? "",
  );
  const [profileFirstName, setProfileFirstName] = useState(
    readStoredAuthUser()?.first_name ?? "",
  );
  const [profileLastName, setProfileLastName] = useState(
    readStoredAuthUser()?.last_name ?? "",
  );
  const [profileTelegram, setProfileTelegram] = useState("@telegram");
  const [profileCurrentPassword, setProfileCurrentPassword] = useState("");
  const [profilePassword, setProfilePassword] = useState("");
  const [profileSaveState, setProfileSaveState] = useState<
    "idle" | "loading" | "success" | "error"
  >("idle");
  const [profileSaveMessage, setProfileSaveMessage] = useState("");
  const [subscriptionPlans, setSubscriptionPlans] = useState<CabinetSubscriptionPlan[]>([]);
  const [subscriptionActionState, setSubscriptionActionState] = useState<
    "idle" | "loading" | "success" | "error"
  >("idle");
  const [subscriptionActionMessage, setSubscriptionActionMessage] = useState("");

  const resetSubscriptionActionState = useCallback(() => {
    setSubscriptionActionState("idle");
    setSubscriptionActionMessage("");
  }, []);

  const openRenewModal = useCallback(() => {
    resetSubscriptionActionState();
    setIsRenewModalOpen(true);
  }, [resetSubscriptionActionState]);

  const closeRenewModal = useCallback(() => {
    setIsRenewModalOpen(false);
    resetSubscriptionActionState();
  }, [resetSubscriptionActionState]);

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

  const subscriptionDetails = useMemo(
    () =>
      subscription && subscription.status !== "none"
        ? [
            { label: "Тариф", value: subscription.planName ?? "Не оформлена" },
            { label: "Активна до", value: subscription.activeUntil ?? "Нет даты" },
            { label: "Осталось дней", value: String(subscription.remainingDays) },
            { label: "Устройств", value: `${devices.length} из ${subscription.maxDevices ?? 0}` },
          ]
        : [],
    [devices, subscription],
  );

  const selectedCountryLink = useMemo(
    () => subscription?.countries.find((country) => country.code === selectedCountry) ?? null,
    [selectedCountry, subscription],
  );

  const overviewStats = useMemo<readonly CabinetOverviewStat[]>(() => {
    const onlineDevicesCount = devices.filter(
      (device) => device.status === "online",
    ).length;

    return cabinetOverviewStats.map((stat) => {
      if (stat.title === "Осталось дней") {
        return {
          ...stat,
          value: subscription ? String(subscription.remainingDays) : "0",
          note:
            subscription?.status === "trial"
              ? "триал активен"
              : subscription?.status === "active"
                ? "подписка активна"
                : subscription?.status === "expired"
                  ? "доступ закончился"
                  : "подписка не оформлена",
        };
      }

      if (stat.title === "Активные устройства") {
        return {
          ...stat,
          value: String(onlineDevicesCount),
          note: subscription && subscription.status !== "none"
            ? `${devices.length} из ${subscription.maxDevices ?? 0} доступных`
            : `${devices.length} устройств в кабинете`,
        };
      }

      return stat;
    });
  }, [devices, subscription]);

  const openServerErrorPage = useCallback(() => {
    navigateToErrorPage(router, "500");
  }, [router]);

  useEffect(() => {
    const token = readAuthToken();

    if (!token) {
      clearAuthSession();
      router.replace("/auth");
      return;
    }

    let isCancelled = false;

    void Promise.all([
      fetchCurrentUser(token),
      fetchCabinetProfile(token),
      fetchCabinetDevices(token),
      fetchCabinetSubscription(token),
      fetchCabinetSubscriptionPlans(token),
    ])
      .then(([user, profile, fetchedDevices, fetchedSubscription, fetchedPlans]) => {
        if (isCancelled) {
          return;
        }

        setCurrentUser(user);
        replaceStoredAuthUser(user);
        setDevices(fetchedDevices);
        setSubscription(fetchedSubscription);
        setSubscriptionPlans(fetchedPlans);
        setSelectedCountry(fetchedSubscription?.countries[0]?.code ?? "");
        setProfileEmail(profile.email);
        setProfileFirstName(profile.firstName);
        setProfileLastName(profile.lastName);
        setProfileTelegram(profile.telegramHandle);
        setProfileSaveState("idle");
        setProfileSaveMessage("");
        setIsSessionResolved(true);
      })
      .catch((error) => {
        if (isCancelled) {
          return;
        }

        if (
          error instanceof AuthRequestError &&
          (error.errorCode === "AUTHENTICATION_FAILED" ||
            error.errorCode === "NOT_AUTHENTICATED")
        ) {
          clearAuthSession();
          router.replace("/auth");
          return;
        }

        openServerErrorPage();
      });

    return () => {
      isCancelled = true;
    };
  }, [openServerErrorPage, router]);

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

  const handleLogout = async () => {
    const token = readAuthToken();

    try {
      if (token) {
        await logoutCurrentUser(token);
      }
    } finally {
      clearAuthSession();
      router.replace("/auth");
    }
  };

  const handleRevokeDevice = async (deviceId: number) => {
    const token = readAuthToken();

    if (!token) {
      clearAuthSession();
      router.replace("/auth");
      return;
    }

    try {
      await revokeCabinetDevice(token, deviceId);
      setDevices((current) => current.filter((device) => device.id !== deviceId));
    } catch {
      openServerErrorPage();
    }
  };

  const handleSaveProfile = async () => {
    const token = readAuthToken();

    if (!token) {
      clearAuthSession();
      router.replace("/auth");
      return;
    }

    setProfileSaveState("loading");
    setProfileSaveMessage("Сохраняем изменения…");

    try {
      const updatedProfile = await updateCabinetProfile(token, {
        email: profileEmail,
        firstName: profileFirstName,
        lastName: profileLastName,
        telegramHandle: profileTelegram,
        currentPassword: profileCurrentPassword || undefined,
        newPassword: profilePassword || undefined,
      });

      const nextUser = currentUser
        ? {
            ...currentUser,
            email: updatedProfile.email,
            first_name: updatedProfile.firstName,
            last_name: updatedProfile.lastName,
          }
        : null;

      setCurrentUser(nextUser);
      if (nextUser) {
        replaceStoredAuthUser(nextUser);
      }
      setProfileEmail(updatedProfile.email);
      setProfileFirstName(updatedProfile.firstName);
      setProfileLastName(updatedProfile.lastName);
      setProfileTelegram(updatedProfile.telegramHandle);
      setProfileCurrentPassword("");
      setProfilePassword("");
      setProfileSaveState("success");
      setProfileSaveMessage("Данные профиля сохранены.");
    } catch {
      setProfileSaveState("error");
      setProfileSaveMessage("Произошла ошибка. Перенаправляем…");
      window.setTimeout(() => {
        openServerErrorPage();
      }, 350);
    }
  };

  const handleSubscriptionCheckout = useCallback(
    async (planCode: string) => {
      const token = readAuthToken();

      if (!token) {
        clearAuthSession();
        router.replace("/auth");
        return;
      }

      setSubscriptionActionState("loading");
      setSubscriptionActionMessage("Создаем платеж…");

      try {
        const checkout = await createCabinetSubscriptionCheckout(token, planCode);
        setSubscriptionActionState("success");
        setSubscriptionActionMessage("Перенаправляем на страницу оплаты…");
        window.location.assign(checkout.checkoutUrl);
      } catch {
        setSubscriptionActionState("error");
        setSubscriptionActionMessage("Не удалось создать платеж.");
      }
    },
    [router],
  );

  if (!isSessionResolved) {
    return (
      <div className={styles.page}>
        <div className={styles.background} aria-hidden="true" />
        <div className={styles.container}>
          <section className={styles.workspace}>
            <div className={styles.content}>
              <section className={styles.pageTop}>
                <div className={styles.pageTitle}>
                  <span className={styles.statusDot} aria-hidden="true" />
                  <div>
                    <h1>Проверка доступа</h1>
                    <p>Подтверждаем текущую сессию…</p>
                  </div>
                </div>
              </section>
            </div>
          </section>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className={styles.background} aria-hidden="true" />

      <div className={styles.container}>
        <section
          className={`${styles.workspace} ${
            isSidebarCompact ? styles.workspaceCompact : ""
          }`}
        >
          <CabinetSidebar
            activeTab={activeTab}
            currentUser={currentUser}
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
            onLogout={() => {
              void handleLogout();
            }}
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
                  className={`${styles.topButton} ${styles.topButtonPrimary}`}
                  onClick={openRenewModal}
                >
                  Продлить
                </button>
              </div>
            </section>

            <section className={styles.mobileCabinetBar}>
              <div className={styles.mobileCabinetTabs} aria-label="Разделы кабинета">
                {mobileCabinetTabs.map((tab) => (
                  <button
                    key={tab.id}
                    type="button"
                    className={`${styles.mobileCabinetTab} ${
                      activeTab === tab.id ? styles.mobileCabinetTabActive : ""
                    }`}
                    onClick={() => setActiveTab(tab.id)}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </section>

            {activeTab === "overview" ? (
              <CabinetOverviewPanel
                stats={overviewStats}
                subscription={subscription}
                devices={devices}
                copyLabel={mainCopyLabel}
                onCopyMainLink={() =>
                  subscription?.mainLink
                    ? void writeToClipboard(subscription.mainLink, "main")
                    : undefined
                }
                onOpenRenew={openRenewModal}
                onOpenTab={setActiveTab}
              />
            ) : null}

            {activeTab === "subscription" && subscription ? (
              <CabinetSubscriptionPanel
                subscription={subscription}
                selectedCountryCode={selectedCountry}
                selectedCountryUrl={selectedCountryLink?.url ?? null}
                details={subscriptionDetails}
                mainCopyLabel={mainCopyLabel}
                serverCopyLabel={serverCopyLabel}
                onOpenRenew={openRenewModal}
                onSelectCountry={setSelectedCountry}
                onCopyMainLink={() =>
                  subscription.mainLink
                    ? void writeToClipboard(subscription.mainLink, "main")
                    : undefined
                }
                onCopyCountryLink={() =>
                  selectedCountryLink
                    ? void writeToClipboard(selectedCountryLink.url, "server")
                    : undefined
                }
              />
            ) : null}

            {activeTab === "devices" ? (
              <CabinetDevicesPanel
                devices={devices}
                onRevokeDevice={(deviceId) => {
                  void handleRevokeDevice(deviceId);
                }}
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
          onClick={closeRenewModal}
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
                  Выберите тариф. Подписка активируется сразу после подтверждения.
                </p>
              </div>
              <button
                type="button"
                className={styles.modalCloseButton}
                onClick={closeRenewModal}
              >
                Закрыть
              </button>
            </div>

            <div className={styles.tariffGrid}>
              {subscriptionPlans.map((tariff) => (
                <article key={tariff.code} className={styles.tariffCard}>
                  <div className={styles.tariffTitle}>{tariff.title}</div>
                  <div className={styles.tariffPrice}>{tariff.priceRub} ₽</div>
                  <div className={styles.tariffNote}>{tariff.description}</div>
                  <button
                    type="button"
                    className={styles.primaryButton}
                    disabled={subscriptionActionState === "loading"}
                    onClick={() => {
                      void handleSubscriptionCheckout(tariff.code);
                    }}
                  >
                    {subscriptionActionState === "loading"
                      ? "Оформление…"
                      : "Перейти к оплате"}
                  </button>
                </article>
              ))}
            </div>
            {subscriptionActionState !== "idle" ? (
              <p className={styles.modalText}>{subscriptionActionMessage}</p>
            ) : null}
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
                <span>Имя</span>
                <input
                  className={styles.settingsInput}
                  type="text"
                  value={profileFirstName}
                  onChange={(event) => setProfileFirstName(event.target.value)}
                />
              </label>

              <label className={styles.settingsField}>
                <span>Фамилия</span>
                <input
                  className={styles.settingsInput}
                  type="text"
                  value={profileLastName}
                  onChange={(event) => setProfileLastName(event.target.value)}
                />
              </label>

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
                <span>Текущий пароль</span>
                <input
                  className={styles.settingsInput}
                  type="password"
                  value={profileCurrentPassword}
                  onChange={(event) => setProfileCurrentPassword(event.target.value)}
                  placeholder="Введите текущий пароль"
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

            <div
              className={`${styles.profileStatus} ${
                profileSaveState !== "idle" ? styles.profileStatusVisible : ""
              } ${
                profileSaveState === "loading" ? styles.profileStatusLoading : ""
              } ${
                profileSaveState === "success"
                  ? styles.profileStatusSuccess
                  : profileSaveState === "error"
                    ? styles.profileStatusError
                    : ""
              }`}
            >
              <span className={styles.profileStatusDot} aria-hidden="true" />
              <span>{profileSaveMessage}</span>
            </div>

            <div className={styles.modalActions}>
              <button
                type="button"
                className={styles.secondaryButton}
                onClick={() => {
                  setIsProfileModalOpen(false);
                  setProfileSaveState("idle");
                  setProfileSaveMessage("");
                }}
              >
                Отмена
              </button>
              <button
                type="button"
                className={styles.primaryButton}
                disabled={profileSaveState === "loading"}
                onClick={() => {
                  void handleSaveProfile();
                }}
              >
                {profileSaveState === "loading" ? "Сохранение…" : "Сохранить"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
