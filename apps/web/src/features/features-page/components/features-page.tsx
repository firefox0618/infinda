import styles from "./features-page.module.css";

import { RevealOnScroll } from "@/shared/ui/reveal-on-scroll";

import {
  featureHighlightCards,
  featuresCta,
  featuresFactItems,
  featuresHero,
} from "../data/features-content";
import { FeaturesIcon } from "./features-icon";

export function FeaturesPage() {
  return (
    <div className={styles.page}>
      <div className={styles.background} aria-hidden="true" />

      <section className={styles.heroSection}>
        <div className={styles.container}>
          <RevealOnScroll>
            <div className={styles.heroContent}>
              <h1 className={styles.heroTitle}>{featuresHero.title}</h1>
              <p className={styles.heroDescription}>{featuresHero.description}</p>
            </div>
          </RevealOnScroll>
        </div>
      </section>

      <section className={styles.gridSection}>
        <div className={styles.container}>
          <div className={styles.grid}>
            {featureHighlightCards.map((card, index) => (
              <RevealOnScroll
                key={card.title}
                delay={index * 80}
                className={styles.cardReveal}
              >
                <article className={styles.card}>
                  <div className={styles.cardIcon} aria-hidden="true">
                    <FeaturesIcon name={card.icon} />
                  </div>
                  <h2 className={styles.cardTitle}>{card.title}</h2>
                  <p className={styles.cardDescription}>{card.description}</p>
                  <div className={styles.cardBadge}>{card.badge}</div>
                </article>
              </RevealOnScroll>
            ))}
          </div>
        </div>
      </section>

      <section className={styles.factsSection}>
        <div className={styles.container}>
          <RevealOnScroll>
            <div className={styles.factsStrip}>
              {featuresFactItems.map((fact) => (
                <div key={fact.value} className={styles.factItem}>
                  <span className={styles.factValue}>{fact.value}</span>
                  <div className={styles.factLabel}>{fact.label}</div>
                </div>
              ))}
            </div>
          </RevealOnScroll>
        </div>
      </section>

      <section className={styles.ctaSection}>
        <div className={styles.ctaGlow} aria-hidden="true" />
        <div className={styles.container}>
          <RevealOnScroll>
            <div className={styles.ctaContent}>
              <h2 className={styles.ctaTitle}>{featuresCta.title}</h2>
              <p className={styles.ctaDescription}>{featuresCta.description}</p>
              <a href="#" className={styles.ctaButton}>
                {featuresCta.buttonLabel}
              </a>
            </div>
          </RevealOnScroll>
        </div>
      </section>
    </div>
  );
}
