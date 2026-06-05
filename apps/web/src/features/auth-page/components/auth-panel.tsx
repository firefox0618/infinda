"use client";

import Link from "next/link";
import { useEffect, useId, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import styles from "./auth-page.module.css";

import { authPageContent } from "../data/auth-content";

type AuthMode = "login" | "register";

type VisibilityState = {
  loginPassword: boolean;
  registerPassword: boolean;
  registerPasswordConfirm: boolean;
};

type FieldErrors = {
  loginEmail?: string;
  loginPassword?: string;
  registerEmail?: string;
  registerPassword?: string;
  registerPasswordConfirm?: string;
  registerTerms?: string;
};

type LoginState = "idle" | "loading" | "success" | "error";

const DEMO_LOGIN = {
  email: "alexey@infinda.com",
  password: "infinda123",
} as const;

export function AuthPanel() {
  const router = useRouter();
  const [mode, setMode] = useState<AuthMode>("login");
  const [showPassword, setShowPassword] = useState<VisibilityState>({
    loginPassword: false,
    registerPassword: false,
    registerPasswordConfirm: false,
  });
  const [errors, setErrors] = useState<FieldErrors>({});
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [registerName, setRegisterName] = useState("");
  const [registerEmail, setRegisterEmail] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");
  const [registerPasswordConfirm, setRegisterPasswordConfirm] = useState("");
  const [registerTerms, setRegisterTerms] = useState(false);
  const [loginState, setLoginState] = useState<LoginState>("idle");
  const [loginStatusText, setLoginStatusText] = useState("");
  const panelId = useId();
  const timersRef = useRef<number[]>([]);

  useEffect(() => {
    return () => {
      timersRef.current.forEach((timerId) => window.clearTimeout(timerId));
      timersRef.current = [];
    };
  }, []);

  const togglePassword = (field: keyof VisibilityState) => {
    setShowPassword((current) => ({
      ...current,
      [field]: !current[field],
    }));
  };

  const validateEmail = (value: string) => /\S+@\S+\.\S+/.test(value);

  const handleLoginSubmit = () => {
    timersRef.current.forEach((timerId) => window.clearTimeout(timerId));
    timersRef.current = [];

    const nextErrors: FieldErrors = {};

    if (!validateEmail(loginEmail)) {
      nextErrors.loginEmail = "Укажи корректный email.";
    }

    if (loginPassword.trim().length < 6) {
      nextErrors.loginPassword = "Пароль должен содержать минимум 6 символов.";
    }

    setErrors(nextErrors);

    if (Object.keys(nextErrors).length > 0) {
      setLoginState("error");
      setLoginStatusText("Проверь email и пароль.");
      return;
    }

    setLoginState("loading");
    setLoginStatusText("Проверка данных…");

    const verifyTimer = window.setTimeout(() => {
      const isMatch =
        loginEmail.trim().toLowerCase() === DEMO_LOGIN.email &&
        loginPassword === DEMO_LOGIN.password;

      if (!isMatch) {
        setLoginState("error");
        setLoginStatusText("Данные не совпадают. Попробуй снова.");
        return;
      }

      setLoginState("success");
      setLoginStatusText("Данные подтверждены. Выполняем вход…");

      const redirectTimer = window.setTimeout(() => {
        router.push("/cabinet");
      }, 900);

      timersRef.current.push(redirectTimer);
    }, 1500);

    timersRef.current.push(verifyTimer);
  };

  const handleRegisterSubmit = () => {
    const nextErrors: FieldErrors = {};

    if (!validateEmail(registerEmail)) {
      nextErrors.registerEmail = "Укажи корректный email.";
    }

    if (registerPassword.trim().length < 6) {
      nextErrors.registerPassword = "Пароль должен содержать минимум 6 символов.";
    }

    if (registerPassword !== registerPasswordConfirm) {
      nextErrors.registerPasswordConfirm = "Пароли должны совпадать.";
    }

    if (!registerTerms) {
      nextErrors.registerTerms = "Нужно принять условия использования.";
    }

    setErrors(nextErrors);
  };

  return (
    <section className={styles.panelSection} aria-labelledby={panelId}>
      <div className={styles.panel} role="tablist" aria-labelledby={panelId}>
        <div className={styles.tabs}>
          <button
            type="button"
            className={`${styles.tabButton} ${
              mode === "login" ? styles.tabButtonActive : ""
            }`}
            onClick={() => setMode("login")}
          >
            {authPageContent.loginTitle}
          </button>
          <button
            type="button"
            className={`${styles.tabButton} ${
              mode === "register" ? styles.tabButtonActive : ""
            }`}
            onClick={() => setMode("register")}
          >
            {authPageContent.registerTitle}
          </button>
        </div>

        {mode === "login" ? (
          <div className={styles.formPanel}>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="login-email">
                Email
              </label>
              <input
                id="login-email"
                className={styles.input}
                type="email"
                value={loginEmail}
                onChange={(event) => setLoginEmail(event.target.value)}
                placeholder="you@example.com"
              />
              {errors.loginEmail ? (
                <span className={styles.errorText}>{errors.loginEmail}</span>
              ) : null}
            </div>

            <div className={styles.field}>
              <label className={styles.label} htmlFor="login-password">
                Пароль
              </label>
              <div className={styles.passwordField}>
                <input
                  id="login-password"
                  className={styles.input}
                  type={showPassword.loginPassword ? "text" : "password"}
                  value={loginPassword}
                  onChange={(event) => setLoginPassword(event.target.value)}
                  placeholder="Минимум 6 символов"
                />
                <button
                  type="button"
                  className={styles.toggleButton}
                  onClick={() => togglePassword("loginPassword")}
                >
                  {showPassword.loginPassword ? "Скрыть" : "Показать"}
                </button>
              </div>
              {errors.loginPassword ? (
                <span className={styles.errorText}>{errors.loginPassword}</span>
              ) : null}
            </div>

            <div className={styles.metaRow}>
              <label className={styles.checkboxRow}>
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(event) => setRememberMe(event.target.checked)}
                  className={styles.checkboxInput}
                />
                <span className={styles.checkboxControl} aria-hidden="true" />
                <span>Запомнить меня</span>
              </label>

              <button type="button" className={styles.textAction}>
                Забыли пароль?
              </button>
            </div>

            <button
              type="button"
              className={`${styles.submitButton} ${
                loginState === "loading"
                  ? styles.submitButtonLoading
                  : loginState === "success"
                    ? styles.submitButtonSuccess
                    : loginState === "error"
                      ? styles.submitButtonError
                      : ""
              }`}
              onClick={handleLoginSubmit}
            >
              <span className={styles.buttonContent}>
                {loginState === "loading" ? (
                  <span className={styles.buttonLoader} aria-hidden="true" />
                ) : null}
                {loginState === "success" ? (
                  <span className={styles.buttonCheck} aria-hidden="true" />
                ) : null}
                <span>
                  {loginState === "loading"
                    ? "Проверка данных"
                    : loginState === "success"
                      ? "Подтверждено"
                      : loginState === "error"
                        ? "Неверно"
                        : "Войти"}
                </span>
              </span>
            </button>

            <div
              className={`${styles.loginStatus} ${
                loginState !== "idle" ? styles.loginStatusVisible : ""
              } ${
                loginState === "loading" ? styles.loginStatusLoading : ""
              } ${
                loginState === "success"
                  ? styles.loginStatusSuccess
                  : loginState === "error"
                    ? styles.loginStatusError
                    : ""
              }`}
            >
              <span className={styles.loginStatusDot} aria-hidden="true" />
              <span>{loginStatusText}</span>
            </div>

            <div className={styles.telegramSection}>
              <button type="button" className={styles.telegramButton}>
                {authPageContent.telegramLoginLabel}
              </button>
            </div>
          </div>
        ) : (
          <div className={styles.formPanel}>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="register-name">
                Имя
              </label>
              <input
                id="register-name"
                className={styles.input}
                type="text"
                value={registerName}
                onChange={(event) => setRegisterName(event.target.value)}
                placeholder="Необязательно"
              />
            </div>

            <div className={styles.field}>
              <label className={styles.label} htmlFor="register-email">
                Email
              </label>
              <input
                id="register-email"
                className={styles.input}
                type="email"
                value={registerEmail}
                onChange={(event) => setRegisterEmail(event.target.value)}
                placeholder="you@example.com"
              />
              {errors.registerEmail ? (
                <span className={styles.errorText}>{errors.registerEmail}</span>
              ) : null}
            </div>

            <div className={styles.field}>
              <label className={styles.label} htmlFor="register-password">
                Пароль
              </label>
              <div className={styles.passwordField}>
                <input
                  id="register-password"
                  className={styles.input}
                  type={showPassword.registerPassword ? "text" : "password"}
                  value={registerPassword}
                  onChange={(event) => setRegisterPassword(event.target.value)}
                  placeholder="Минимум 6 символов"
                />
                <button
                  type="button"
                  className={styles.toggleButton}
                  onClick={() => togglePassword("registerPassword")}
                >
                  {showPassword.registerPassword ? "Скрыть" : "Показать"}
                </button>
              </div>
              {errors.registerPassword ? (
                <span className={styles.errorText}>{errors.registerPassword}</span>
              ) : null}
            </div>

            <div className={styles.field}>
              <label className={styles.label} htmlFor="register-password-confirm">
                Подтверждение пароля
              </label>
              <div className={styles.passwordField}>
                <input
                  id="register-password-confirm"
                  className={styles.input}
                  type={showPassword.registerPasswordConfirm ? "text" : "password"}
                  value={registerPasswordConfirm}
                  onChange={(event) =>
                    setRegisterPasswordConfirm(event.target.value)
                  }
                  placeholder="Повтори пароль"
                />
                <button
                  type="button"
                  className={styles.toggleButton}
                  onClick={() => togglePassword("registerPasswordConfirm")}
                >
                  {showPassword.registerPasswordConfirm ? "Скрыть" : "Показать"}
                </button>
              </div>
              {errors.registerPasswordConfirm ? (
                <span className={styles.errorText}>
                  {errors.registerPasswordConfirm}
                </span>
              ) : null}
            </div>

            <label className={styles.checkboxRow}>
              <input
                type="checkbox"
                checked={registerTerms}
                onChange={(event) => setRegisterTerms(event.target.checked)}
                className={styles.checkboxInput}
              />
              <span className={styles.checkboxControl} aria-hidden="true" />
              <span>
                Принимаю{" "}
                <Link href="/auth" className={styles.inlineLink}>
                  условия использования
                </Link>{" "}
                и{" "}
                <Link href="/auth" className={styles.inlineLink}>
                  политику конфиденциальности
                </Link>
              </span>
            </label>
            {errors.registerTerms ? (
              <span className={styles.errorText}>{errors.registerTerms}</span>
            ) : null}

            <button
              type="button"
              className={styles.submitButton}
              onClick={handleRegisterSubmit}
            >
              Зарегистрироваться
            </button>

            <div className={styles.telegramSection}>
              <button type="button" className={styles.telegramButton}>
                {authPageContent.telegramRegisterLabel}
              </button>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
