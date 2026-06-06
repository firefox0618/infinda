"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import {
  AuthRequestError,
  fetchCurrentUser,
  logoutCurrentUser,
} from "@/shared/auth/auth-client";
import {
  clearAuthSession,
  readAuthToken,
  readStoredAuthUser,
  replaceStoredAuthUser,
} from "@/shared/auth/auth-storage";
import type { AuthUser } from "@/shared/auth/auth-types";
import {
  fetchCabinetDevices,
  fetchCabinetProfile,
  fetchCabinetSubscription,
  fetchCabinetSubscriptionPlans,
  revokeCabinetDevice,
  type CabinetSubscriptionPlan,
} from "../api/cabinet-client";
import { cabinetOverviewStats } from "../data/cabinet-content";
import type {
  CabinetDevice,
  CabinetOverviewStat,
  CabinetSubscription,
  CabinetTab,
} from "../components/cabinet-models";
import { resolveCabinetSection } from "../constants/cabinet-tabs";
import { useCabinetClipboardState } from "./use-cabinet-clipboard-state";
import { useCabinetProfileState } from "./use-cabinet-profile-state";
import { useCabinetSubscriptionActions } from "./use-cabinet-subscription-actions";

type UseCabinetPageStateArgs = {
  onAuthRequired: () => void;
  onServerError: () => void;
};

function getInitialStoredUser() {
  return readStoredAuthUser();
}

export function useCabinetPageState({
  onAuthRequired,
  onServerError,
}: UseCabinetPageStateArgs) {
  const [activeTab, setActiveTab] = useState<CabinetTab>("overview");
  const [isSidebarCompact, setIsSidebarCompact] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [selectedCountry, setSelectedCountry] = useState("");
  const [devices, setDevices] = useState<CabinetDevice[]>([]);
  const [subscription, setSubscription] = useState<CabinetSubscription | null>(null);
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(getInitialStoredUser());
  const [isSessionResolved, setIsSessionResolved] = useState(false);
  const [subscriptionPlans, setSubscriptionPlans] = useState<CabinetSubscriptionPlan[]>([]);
  const { mainCopyLabel, serverCopyLabel, writeToClipboard } =
    useCabinetClipboardState();
  const {
    profile,
    profileSaveMessage,
    profileSaveState,
    closeProfileModal: resetProfileState,
    handleSaveProfile,
    hydrateProfile,
    setProfileField,
  } = useCabinetProfileState({
    currentUser,
    onAuthRequired,
    onServerError,
    onUserUpdated: setCurrentUser,
  });
  const {
    isRenewModalOpen,
    subscriptionActionMessage,
    subscriptionActionState,
    closeRenewModal,
    handleSubscriptionCheckout,
    openRenewModal,
  } = useCabinetSubscriptionActions(onAuthRequired);

  const currentSection = useMemo(
    () => resolveCabinetSection(activeTab),
    [activeTab],
  );

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

  useEffect(() => {
    const token = readAuthToken();

    if (!token) {
      clearAuthSession();
      onAuthRequired();
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
      .then(([user, fetchedProfile, fetchedDevices, fetchedSubscription, fetchedPlans]) => {
        if (isCancelled) {
          return;
        }

        setCurrentUser(user);
        replaceStoredAuthUser(user);
        setDevices(fetchedDevices);
        setSubscription(fetchedSubscription);
        setSubscriptionPlans(fetchedPlans);
        setSelectedCountry(fetchedSubscription?.countries[0]?.code ?? "");
        hydrateProfile({
          email: fetchedProfile.email,
          firstName: fetchedProfile.firstName,
          lastName: fetchedProfile.lastName,
          telegramHandle: fetchedProfile.telegramHandle,
        });
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
          onAuthRequired();
          return;
        }

        onServerError();
      });

    return () => {
      isCancelled = true;
    };
  }, [hydrateProfile, onAuthRequired, onServerError]);

  const handleLogout = useCallback(async () => {
    const token = readAuthToken();

    try {
      if (token) {
        await logoutCurrentUser(token);
      }
    } finally {
      clearAuthSession();
      onAuthRequired();
    }
  }, [onAuthRequired]);

  const handleRevokeDevice = useCallback(
    async (deviceId: number) => {
      const token = readAuthToken();

      if (!token) {
        clearAuthSession();
        onAuthRequired();
        return;
      }

      try {
        await revokeCabinetDevice(token, deviceId);
        setDevices((current) => current.filter((device) => device.id !== deviceId));
      } catch {
        onServerError();
      }
    },
    [onAuthRequired, onServerError],
  );

  const closeProfileModal = useCallback(() => {
    setIsProfileModalOpen(false);
    resetProfileState();
  }, [resetProfileState]);

  return {
    activeTab,
    currentSection,
    currentUser,
    devices,
    isMobileSidebarOpen,
    isProfileModalOpen,
    isRenewModalOpen,
    isSessionResolved,
    isSidebarCompact,
    mainCopyLabel,
    overviewStats,
    profile,
    profileSaveMessage,
    profileSaveState,
    selectedCountry,
    selectedCountryLink,
    serverCopyLabel,
    subscription,
    subscriptionActionMessage,
    subscriptionActionState,
    subscriptionDetails,
    subscriptionPlans,
    closeProfileModal,
    closeRenewModal,
    handleLogout,
    handleRevokeDevice,
    handleSaveProfile,
    handleSubscriptionCheckout,
    openRenewModal,
    setActiveTab,
    setIsMobileSidebarOpen,
    setIsProfileModalOpen,
    setIsSidebarCompact,
    setProfileField,
    setSelectedCountry,
    writeToClipboard,
  };
}
