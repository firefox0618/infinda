"use client";

import Link from "next/link";

import styles from "./error-page.module.css";

import { SUPPORT_TELEGRAM_URL } from "@/shared/config/support-links";

import type { ErrorPageCode } from "../data/error-content";
import { errorPageContentMap } from "../data/error-content";

type ErrorPageProps = {
  code: ErrorPageCode;
};

export function ErrorPage({ code }: ErrorPageProps) {
  const content = errorPageContentMap[code];

  return (
    <div className={`${styles.page} ${styles[content.modeClass]}`}>
      <section className={styles.content}>
        <div className={styles.badge}>
          <span className={styles.badgeDot} aria-hidden="true" />
          <span>{content.badge}</span>
        </div>

        <h1 className={styles.code}>{code}</h1>

        <h2 className={styles.title}>{content.title}</h2>

        <p className={styles.text}>{content.text}</p>

        <div className={styles.actions}>
          <Link className={`${styles.button} ${styles.buttonPrimary}`} href="/">
            На главную
          </Link>
          <button
            type="button"
            className={`${styles.button} ${styles.buttonSecondary}`}
            onClick={() => window.location.reload()}
          >
            Обновить страницу
          </button>
          <a
            className={`${styles.button} ${styles.buttonSecondary}`}
            href={SUPPORT_TELEGRAM_URL}
            target="_blank"
            rel="noreferrer"
          >
            Написать в поддержку
          </a>
        </div>

        <div className={styles.hint}>
          <div className={styles.hintIcon}>i</div>
          <div>
            Если ошибка повторяется, отправьте в поддержку код ошибки и адрес
            страницы. Это поможет быстрее найти проблему.
          </div>
        </div>
      </section>

      <section className={styles.visual}>
        <div className={styles.halo} />

        <div className={styles.routeCard}>
          <div className={styles.routeInner}>
            <div className={styles.miniTop}>
              <div className={styles.miniTitle}>Состояние запроса</div>
              <div className={styles.miniStatus}>{content.status}</div>
            </div>

            <div className={styles.network}>
              <div className={`${styles.routeLine} ${styles.routeLineLeft}`} />
              <div className={`${styles.routeLine} ${styles.routeLineRight}`} />

              <div className={`${styles.node} ${styles.nodeUser}`}>⌂</div>

              <div className={`${styles.node} ${styles.nodeCenter}`}>
                <div className={styles.centerGlow} />
                <div className={styles.centerRing} />
                <span className={styles.centerSymbol}>{content.center}</span>
              </div>

              <div className={`${styles.node} ${styles.nodeServer}`}>☁</div>
            </div>

            <div className={styles.miniMessage}>
              <strong>{content.miniTitle}</strong>
              <span>{content.miniText}</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
