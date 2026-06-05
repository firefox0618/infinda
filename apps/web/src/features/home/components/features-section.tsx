import styles from "./features-section.module.css";

import { FeatureIcon } from "./feature-icon";
import { featureCards, homeFeaturesIntro } from "../data/home-content";
import { RevealOnScroll } from "@/shared/ui/reveal-on-scroll";

export function FeaturesSection() {
  return (
    <section className={styles.section} id="features">
      <div className={styles.inner}>
        <RevealOnScroll>
          <div className={styles.head}>
            <h2 className={styles.title}>{homeFeaturesIntro.title}</h2>
            <p className={styles.description}>{homeFeaturesIntro.description}</p>
          </div>
        </RevealOnScroll>

        <div className={styles.grid}>
          {featureCards.map((feature, index) => (
            <RevealOnScroll
              key={feature.title}
              delay={index * 110}
              className={styles.cardReveal}
            >
              <article className={styles.card}>
                <div className={styles.icon} aria-hidden="true">
                  <FeatureIcon name={feature.icon} />
                </div>
                <h3 className={styles.cardTitle}>{feature.title}</h3>
                <p className={styles.cardDescription}>{feature.description}</p>
              </article>
            </RevealOnScroll>
          ))}
        </div>
      </div>
    </section>
  );
}
