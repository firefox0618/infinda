import type { PublicSubscriptionSummaryDto } from "@infinda/shared/contracts/public-subscription";

import styles from "./public-subscription-page.module.css";

type PublicRouteCardProps = {
  route: PublicSubscriptionSummaryDto["countries"][number];
};

export function PublicRouteCard({ route }: PublicRouteCardProps) {
  return (
    <article className={styles.routeCard}>
      <div className={styles.routeCardHead}>
        <div className={styles.routeCountry}>{route.label}</div>
        <div className={styles.routeCardMeta}>
          {route.is_provisioned ? (
            <span className={styles.routeProvisionedBadge}>Provisioned</span>
          ) : null}
          <div className={styles.routeCode}>{route.code.toUpperCase()}</div>
        </div>
      </div>
      <div className={styles.routeUrlBox}>
        <code className={styles.routeUrlCode}>{route.url}</code>
      </div>
      <div className={styles.routeActions}>
        {route.client_links.map((link) => (
          <a
            key={link.code}
            className={link.kind === "happ" ? styles.routePrimaryAction : styles.routeSecondaryAction}
            href={link.url}
          >
            {link.label}
          </a>
        ))}
      </div>
    </article>
  );
}
