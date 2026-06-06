"use client";

import { useCallback, useState } from "react";

import { clearAuthSession, readAuthToken, replaceStoredAuthUser } from "@/shared/auth/auth-storage";
import type { AuthUser } from "@/shared/auth/auth-types";
import { updateCabinetProfile } from "../api/cabinet-client";

export type CabinetProfileFormState = {
  email: string;
  firstName: string;
  lastName: string;
  telegramHandle: string;
  currentPassword: string;
  newPassword: string;
};

type ProfileSaveState = "idle" | "loading" | "success" | "error";

type UseCabinetProfileStateArgs = {
  currentUser: AuthUser | null;
  onAuthRequired: () => void;
  onServerError: () => void;
  onUserUpdated: (user: AuthUser | null) => void;
};

function createInitialProfileState(user: AuthUser | null): CabinetProfileFormState {
  return {
    email: user?.email ?? "",
    firstName: user?.first_name ?? "",
    lastName: user?.last_name ?? "",
    telegramHandle: "@telegram",
    currentPassword: "",
    newPassword: "",
  };
}

export function useCabinetProfileState({
  currentUser,
  onAuthRequired,
  onServerError,
  onUserUpdated,
}: UseCabinetProfileStateArgs) {
  const [profile, setProfile] = useState<CabinetProfileFormState>(
    createInitialProfileState(currentUser),
  );
  const [profileSaveState, setProfileSaveState] = useState<ProfileSaveState>("idle");
  const [profileSaveMessage, setProfileSaveMessage] = useState("");

  const hydrateProfile = useCallback((nextProfile: Omit<CabinetProfileFormState, "currentPassword" | "newPassword">) => {
    setProfile({
      ...nextProfile,
      currentPassword: "",
      newPassword: "",
    });
    setProfileSaveState("idle");
    setProfileSaveMessage("");
  }, []);

  const closeProfileModal = useCallback(() => {
    setProfileSaveState("idle");
    setProfileSaveMessage("");
  }, []);

  const setProfileField = useCallback(
    (field: keyof CabinetProfileFormState, value: string) => {
      setProfile((current) => ({ ...current, [field]: value }));
    },
    [],
  );

  const handleSaveProfile = useCallback(async () => {
    const token = readAuthToken();

    if (!token) {
      clearAuthSession();
      onAuthRequired();
      return;
    }

    setProfileSaveState("loading");
    setProfileSaveMessage("Сохраняем изменения…");

    try {
      const updatedProfile = await updateCabinetProfile(token, {
        email: profile.email,
        firstName: profile.firstName,
        lastName: profile.lastName,
        telegramHandle: profile.telegramHandle,
        currentPassword: profile.currentPassword || undefined,
        newPassword: profile.newPassword || undefined,
      });

      const nextUser = currentUser
        ? {
            ...currentUser,
            email: updatedProfile.email,
            first_name: updatedProfile.firstName,
            last_name: updatedProfile.lastName,
          }
        : null;

      onUserUpdated(nextUser);
      if (nextUser) {
        replaceStoredAuthUser(nextUser);
      }

      setProfile({
        email: updatedProfile.email,
        firstName: updatedProfile.firstName,
        lastName: updatedProfile.lastName,
        telegramHandle: updatedProfile.telegramHandle,
        currentPassword: "",
        newPassword: "",
      });
      setProfileSaveState("success");
      setProfileSaveMessage("Данные профиля сохранены.");
    } catch {
      setProfileSaveState("error");
      setProfileSaveMessage("Произошла ошибка. Перенаправляем…");
      window.setTimeout(() => {
        onServerError();
      }, 350);
    }
  }, [currentUser, onAuthRequired, onServerError, onUserUpdated, profile]);

  return {
    profile,
    profileSaveMessage,
    profileSaveState,
    closeProfileModal,
    handleSaveProfile,
    hydrateProfile,
    setProfileField,
  };
}
