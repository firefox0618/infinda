import type { PublicSubscriptionInstallGuideDto } from "@infinda/shared/contracts/public-subscription";

import styles from "./public-subscription-page.module.css";

type PublicInstallGuidesProps = {
  installGuides: PublicSubscriptionInstallGuideDto[];
};

export function PublicInstallGuides({
  installGuides,
}: PublicInstallGuidesProps) {
  return (
    <section className={styles.section}>
      <div className={styles.sectionHeader}>
        <div>
          <p className={styles.sectionEyebrow}>Установка</p>
          <h2 className={styles.sectionTitle}>Выберите платформу для Happ</h2>
        </div>
        <p className={styles.sectionDescription}>
          Сначала установите клиент, затем вернитесь к этой подписке и откройте
          feed или прямую ссылку на нужный маршрут.
        </p>
      </div>
      <div className={styles.installGrid}>
        {installGuides.map((guide) => (
          <article key={guide.code} className={styles.installCard}>
            <div className={styles.installTitle}>{guide.title}</div>
            <p className={styles.installDescription}>{guide.description}</p>
            <div className={styles.installLinks}>
              {guide.links.map((link) => (
                <a key={`${guide.code}-${link.label}`} className={styles.installLink} href={link.url}>
                  {link.label}
                </a>
              ))}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
