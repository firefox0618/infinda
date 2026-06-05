"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import styles from "./site-header.module.css";

import { MobileNavigation } from "./mobile-navigation";
import { siteNavigationItems } from "./site-content";

export function SiteHeader() {
  const pathname = usePathname();
  const shouldShowAuthCta = pathname !== "/auth" && pathname !== "/cabinet";

  return (
    <header className={styles.header}>
      <div className={styles.inner}>
        <Link href="/" className={styles.brand}>
          <span className={styles.brandMark} aria-hidden="true" />
          <span className={styles.brandText}>INFINDA</span>
        </Link>

        <nav className={styles.nav} aria-label="Основная навигация">
          {siteNavigationItems.map((item) => (
            <Link
              key={item.label}
              href={item.href}
              className={`${styles.navLink} ${
                pathname === item.href ? styles.navLinkActive : ""
              }`}
            >
              <span className={styles.navLabel}>{item.label}</span>
            </Link>
          ))}
        </nav>

        {shouldShowAuthCta ? (
          <Link href="/auth" className={styles.cta}>
            Вход
          </Link>
        ) : (
          <span className={`${styles.cta} ${styles.ctaHidden}`} aria-hidden="true">
            Вход
          </span>
        )}

        <MobileNavigation items={siteNavigationItems} />
      </div>
    </header>
  );
}
