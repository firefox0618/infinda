"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

import styles from "./mobile-navigation.module.css";

type MobileNavigationItem = {
  label: string;
  href: string;
};

type MobileNavigationProps = {
  items: readonly MobileNavigationItem[];
};

export function MobileNavigation({ items }: MobileNavigationProps) {
  const [isOpen, setIsOpen] = useState(false);
  const pathname = usePathname();
  const shouldShowAuthCta = pathname !== "/auth";

  const toggleMenu = () => {
    setIsOpen((currentValue) => !currentValue);
  };

  const closeMenu = () => {
    setIsOpen(false);
  };

  return (
    <div className={styles.wrapper}>
      <button
        type="button"
        className={styles.trigger}
        aria-label={isOpen ? "Закрыть меню" : "Открыть меню"}
        aria-expanded={isOpen}
        onClick={toggleMenu}
      >
        <span className={styles.triggerLine} />
        <span className={styles.triggerLine} />
        <span className={styles.triggerLine} />
      </button>

      <div
        className={`${styles.overlay} ${isOpen ? styles.overlayVisible : ""}`}
        onClick={closeMenu}
      />

      <div
        className={`${styles.panel} ${isOpen ? styles.panelOpen : ""}`}
        aria-hidden={!isOpen}
      >
        <div className={styles.panelHead}>
          <div className={styles.panelTitle}>Меню</div>
          <button
            type="button"
            className={styles.closeButton}
            aria-label="Закрыть меню"
            onClick={closeMenu}
          >
            <span />
            <span />
          </button>
        </div>

        <nav className={styles.nav} aria-label="Мобильная навигация">
          {items.map((item) => (
            <Link
              key={item.label}
              href={item.href}
              className={`${styles.navLink} ${
                pathname === item.href ? styles.navLinkActive : ""
              }`}
              onClick={closeMenu}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        {shouldShowAuthCta ? (
          <Link href="/auth" className={styles.loginButton} onClick={closeMenu}>
            Вход
          </Link>
        ) : null}
      </div>
    </div>
  );
}
