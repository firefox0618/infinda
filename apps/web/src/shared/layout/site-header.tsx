import styles from "./site-header.module.css";

import { MobileNavigation } from "./mobile-navigation";
import { siteNavigationItems } from "./site-content";

export function SiteHeader() {
  return (
    <header className={styles.header}>
      <div className={styles.inner}>
        <a href="#" className={styles.brand}>
          <span className={styles.brandMark} aria-hidden="true" />
          <span className={styles.brandText}>INFINDA</span>
        </a>

        <nav className={styles.nav} aria-label="Основная навигация">
          {siteNavigationItems.map((item) => (
            <a key={item.label} href={item.href} className={styles.navLink}>
              <span className={styles.navLabel}>{item.label}</span>
            </a>
          ))}
        </nav>

        <a href="#" className={styles.cta}>
          Вход
        </a>

        <MobileNavigation items={siteNavigationItems} />
      </div>
    </header>
  );
}
