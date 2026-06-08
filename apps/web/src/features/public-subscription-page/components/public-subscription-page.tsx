"use client";

import { useState } from "react";

import type { PublicSubscriptionSummaryDto } from "@infinda/shared/contracts/public-subscription";

import { getStoredPublicDeviceKey } from "./public-device-key";
import { PublicInstallGuides } from "./public-install-guides";
import { PublicRouteCard } from "./public-route-card";
import { PublicSubscriptionTouch } from "./public-subscription-touch";
import styles from "./public-subscription-page.module.css";

type PublicSubscriptionPageProps = {
  token: string;
  subscription: PublicSubscriptionSummaryDto;
};

function formatDate(dateValue: string) {
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  }).format(new Date(dateValue));
}

function getStatusLabel(status: PublicSubscriptionSummaryDto["status"]) {
  switch (status) {
    case "trial":
      return "Триал";
    case "active":
      return "Активна";
    case "expired":
      return "Истекла";
    case "pending_payment":
      return "Ожидает оплату";
  }
}

export function PublicSubscriptionPage({
  token,
  subscription: initialSubscription,
}: PublicSubscriptionPageProps) {
  const [subscription, setSubscription] = useState(initialSubscription);
  const [deviceKey, setDeviceKey] = useState<string | null>(() => getStoredPublicDeviceKey(token));

  async function refreshSummary() {
    const nextDeviceKey = getStoredPublicDeviceKey(token);
    const response = await fetch(`/api/subscription/public/${token}/summary`, {
      cache: "no-store",
      headers: nextDeviceKey ? { "X-Device-Key": nextDeviceKey } : undefined,
    });
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as PublicSubscriptionSummaryDto;
    setDeviceKey(nextDeviceKey);
    setSubscription(payload);
  }

  const feedPath = deviceKey
    ? `/sub/${token}/feed?device_key=${encodeURIComponent(deviceKey)}`
    : subscription.feed_link || `/sub/${token}/feed`;
  const happPath = subscription.happ_link;

  return (
    <div className={styles.page}>
      <div className={styles.background} aria-hidden="true" />
      <section className={styles.hero}>
        <p className={styles.eyebrow}>Public Subscription</p>
        <h1 className={styles.title}>{subscription.plan_name}</h1>
        <p className={styles.description}>
          Публичная страница доступа для установки и импорта подписки. Здесь
          пользователь видит срок действия, доступные маршруты и быстрые действия
          для Happ и других клиентов.
        </p>
        <p className={styles.description}>
          {subscription.uses_provisioned_access
            ? `Для устройства ${subscription.resolved_device_name ?? "с текущего IP"} уже подготовлены реальные provisioned credentials по ${subscription.provisioned_route_count} маршрутам.`
            : "Если устройство уже известно системе, эта страница автоматически подставит его provisioned credentials. Иначе пока показываются fallback-ссылки."}
        </p>
        <PublicSubscriptionTouch
          token={token}
          onTouched={() => {
            void refreshSummary();
          }}
        />
      </section>

      <section className={styles.grid}>
        <article className={styles.card}>
          <div className={styles.cardLabel}>Статус</div>
          <div
            className={`${styles.cardValue} ${
              subscription.status === "active" || subscription.status === "trial"
                ? styles.cardValueActive
                : styles.cardValueMuted
            }`}
          >
            {getStatusLabel(subscription.status)}
          </div>
        </article>
        <article className={styles.card}>
          <div className={styles.cardLabel}>Доступ активен до</div>
          <div className={styles.cardValue}>{formatDate(subscription.active_until)}</div>
        </article>
        <article className={styles.card}>
          <div className={styles.cardLabel}>Осталось дней</div>
          <div className={styles.cardValue}>{subscription.remaining_days}</div>
        </article>
        <article className={styles.card}>
          <div className={styles.cardLabel}>Лимит устройств</div>
          <div className={styles.cardValue}>{subscription.max_devices}</div>
        </article>
      </section>

      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <div>
            <p className={styles.sectionEyebrow}>Быстрый старт</p>
            <h2 className={styles.sectionTitle}>Откройте подписку за пару действий</h2>
          </div>
          <p className={styles.sectionDescription}>
            Если Happ уже установлен, начните с прямого открытия. Если нет,
            сначала установите клиент ниже, а затем вернитесь к этой странице.
          </p>
        </div>
        <div className={styles.quickActions}>
          {subscription.client_links.map((link) => (
            <a
              key={link.code}
              className={link.kind === "happ" ? styles.quickActionPrimary : styles.quickActionSecondary}
              href={link.url}
            >
              {link.label}
            </a>
          ))}
          <a className={styles.quickActionSecondary} href={feedPath}>
            Raw feed
          </a>
        </div>
      </section>

      <PublicInstallGuides installGuides={subscription.install_guides} />

      <section className={styles.section}>
        <div className={styles.routesHeader}>
          <div>
            <p className={styles.sectionEyebrow}>Маршруты</p>
            <h2 className={styles.routesTitle}>Импорт по странам и серверам</h2>
          </div>
          <div className={styles.actions}>
            <a className={styles.linkBadge} href={feedPath}>
              Открыть feed
            </a>
            <a className={styles.linkBadgeSecondary} href={happPath}>
              Открыть Happ wrapper
            </a>
          </div>
        </div>
        <div className={styles.routesGrid}>
          {subscription.countries.map((route) => (
            <PublicRouteCard key={route.code} route={route} />
          ))}
        </div>
      </section>
    </div>
  );
}
