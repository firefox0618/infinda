"use client";

import { useCallback } from "react";
import { useRouter } from "next/navigation";

import { navigateToErrorPage } from "@/shared/navigation/error-page-navigation";

import styles from "./cabinet-page.module.css";
import { CabinetDevicesPanel } from "./cabinet-devices-panel";
import { CabinetOverviewPanel } from "./cabinet-overview-panel";
import { CabinetProfileModal } from "./cabinet-profile-modal";
import { CabinetRenewModal } from "./cabinet-renew-modal";
import { CabinetSidebar } from "./cabinet-sidebar";
import { CabinetSubscriptionPanel } from "./cabinet-subscription-panel";
import { CabinetSupportPanel } from "./cabinet-support-panel";
import { mobileCabinetTabs } from "../constants/cabinet-tabs";
import { useCabinetPageState } from "../hooks/use-cabinet-page-state";
import { useCabinetSupportState } from "../hooks/use-cabinet-support-state";

export function CabinetPage() {
  const router = useRouter();
  const handleAuthRequired = useCallback(() => {
    router.replace("/auth");
  }, [router]);
  const handleServerError = useCallback(() => {
    navigateToErrorPage(router, "500");
  }, [router]);
  const state = useCabinetPageState({
    onAuthRequired: handleAuthRequired,
    onServerError: handleServerError,
  });
  const support = useCabinetSupportState({
    onAuthRequired: handleAuthRequired,
  });

  if (!state.isSessionResolved) {
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
            state.isSidebarCompact ? styles.workspaceCompact : ""
          }`}
        >
          <CabinetSidebar
            activeTab={state.activeTab}
            currentUser={state.currentUser}
            isCompact={state.isSidebarCompact}
            isMobileOpen={state.isMobileSidebarOpen}
            onToggleCompact={() => {
              if (typeof window !== "undefined" && window.innerWidth <= 980) {
                state.setIsMobileSidebarOpen((current) => !current);
                return;
              }

              state.setIsSidebarCompact((current) => !current);
            }}
            onCloseMobile={() => state.setIsMobileSidebarOpen(false)}
            onOpenProfile={() => state.setIsProfileModalOpen(true)}
            onLogout={() => {
              void state.handleLogout();
            }}
            onSelectTab={state.setActiveTab}
          />

          <div className={styles.content}>
            <section className={styles.pageTop}>
              <div className={styles.pageTitle}>
                <span className={styles.statusDot} aria-hidden="true" />
                <div>
                  <h1>{state.currentSection.title}</h1>
                  <p>{state.currentSection.subtitle}</p>
                </div>
              </div>

              <div className={styles.pageActions}>
                <button
                  type="button"
                  data-testid="cabinet-open-renew-button"
                  className={`${styles.topButton} ${styles.topButtonPrimary}`}
                  onClick={state.openRenewModal}
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
                      state.activeTab === tab.id ? styles.mobileCabinetTabActive : ""
                    }`}
                    onClick={() => state.setActiveTab(tab.id)}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </section>

            {state.activeTab === "overview" ? (
              <CabinetOverviewPanel
                accessState={state.accessState}
                stats={state.overviewStats}
                subscription={state.subscription}
                devices={state.devices}
                copyLabel={state.mainCopyLabel}
                onCopyMainLink={() =>
                  state.subscription?.mainLink
                    ? void state.writeToClipboard(state.subscription.mainLink, "main")
                    : undefined
                }
                onSyncAccess={() => {
                  void state.handleSyncAccess();
                }}
                onOpenRenew={state.openRenewModal}
                onOpenTab={state.setActiveTab}
              />
            ) : null}

            {state.activeTab === "subscription" && state.subscription ? (
              <CabinetSubscriptionPanel
                subscription={state.subscription}
                selectedCountryCode={state.selectedCountry}
                selectedCountryUrl={state.selectedCountryLink?.url ?? null}
                selectedCountryClientLinks={state.selectedCountryLink?.client_links ?? []}
                details={state.subscriptionDetails}
                mainCopyLabel={state.mainCopyLabel}
                serverCopyLabel={state.serverCopyLabel}
                onOpenRenew={state.openRenewModal}
                onSelectCountry={state.setSelectedCountry}
                onCopyMainLink={() =>
                  state.subscription?.mainLink
                    ? void state.writeToClipboard(state.subscription.mainLink, "main")
                    : undefined
                }
                onCopyCountryLink={() =>
                  state.selectedCountryLink
                    ? void state.writeToClipboard(state.selectedCountryLink.url, "server")
                    : undefined
                }
              />
            ) : null}

            {state.activeTab === "devices" ? (
              <CabinetDevicesPanel
                actionMessage={state.deviceActionMessage}
                actionState={state.deviceActionState}
                devices={state.devices}
                onRepairDevice={(deviceId, reason) => {
                  void state.handleRepairDevice(deviceId, reason);
                }}
                onRevokeDevice={(deviceId, reason) => {
                  void state.handleRevokeDevice(deviceId, reason);
                }}
              />
            ) : null}

            {state.activeTab === "support" ? (
              <CabinetSupportPanel
                assignedAdminName={support.conversation?.assignedAdminName ?? null}
                attachedFiles={support.attachedFiles}
                errorMessage={support.errorMessage}
                loadState={support.loadState}
                message={support.messageDraft}
                messages={support.messages}
                sendState={support.sendState}
                status={support.conversation?.status ?? null}
                onChangeMessage={support.setMessageDraft}
                onChangeFiles={support.handleChangeFiles}
                onRemoveFile={support.handleRemoveFile}
                onSendMessage={support.handleSendMessage}
              />
            ) : null}
          </div>
        </section>
      </div>

      <CabinetRenewModal
        isOpen={state.isRenewModalOpen}
        plans={state.subscriptionPlans}
        actionState={state.subscriptionActionState}
        actionMessage={state.subscriptionActionMessage}
        onClose={state.closeRenewModal}
        onCheckout={(planCode) => {
          void state.handleSubscriptionCheckout(planCode);
        }}
      />

      <CabinetProfileModal
        isOpen={state.isProfileModalOpen}
        profile={state.profile}
        saveState={state.profileSaveState}
        saveMessage={state.profileSaveMessage}
        telegramLink={state.telegramLink}
        telegramLinkActionMessage={state.telegramLinkActionMessage}
        telegramLinkActionState={state.telegramLinkActionState}
        telegramLinkDeepLinkUrl={state.telegramLinkDeepLinkUrl}
        onClose={state.closeProfileModal}
        onCreateTelegramLink={state.handleCreateTelegramLink}
        onSave={() => {
          void state.handleSaveProfile();
        }}
        onChangeField={state.setProfileField}
        onUnlinkTelegram={() => {
          void state.handleUnlinkTelegram();
        }}
      />
    </div>
  );
}
