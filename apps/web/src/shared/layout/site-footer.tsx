import styles from "./site-footer.module.css";

import { siteFooterColumns } from "./site-content";

export function SiteFooter() {
  return (
    <footer className={styles.footer}>
      <div className={styles.inner}>
        <div className={styles.topRow}>
          <div className={styles.brandBlock}>
            <div className={styles.brandName}>INFINDA</div>
            <p className={styles.brandNote}>
              Приватная сеть без лишнего шума. Быстрый доступ, тихая
              маршрутизация и понятный интерфейс.
            </p>
          </div>

          <div className={styles.grid}>
            {siteFooterColumns.map((column) => (
              <div key={column.title}>
                <h4 className={styles.title}>{column.title}</h4>
                {column.links.map((link) => (
                  <a key={link} href="#" className={styles.link}>
                    {link}
                  </a>
                ))}
              </div>
            ))}
          </div>
        </div>

        <div className={styles.bottom}>
          <div>© 2026 INFINDA · Private Network</div>
          <div className={styles.bottomLinks}>
            <a href="#">Telegram</a>
            <a href="#">Русский</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
