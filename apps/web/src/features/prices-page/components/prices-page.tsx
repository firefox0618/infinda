import styles from "./prices-page.module.css";

import { Accordion } from "@/shared/ui/accordion";
import { RevealOnScroll } from "@/shared/ui/reveal-on-scroll";

import {
  compareItems,
  pricePlans,
  pricesCta,
  pricesFaqItems,
  pricesHero,
} from "../data/prices-content";
import { PricesIcon } from "./prices-icon";

export function PricesPage() {
  return (
    <div className={styles.page}>
      <div className={styles.background} aria-hidden="true" />

      <section className={styles.heroSection}>
        <div className={styles.container}>
          <RevealOnScroll>
            <div className={styles.heroContent}>
              <h1 className={styles.heroTitle}>{pricesHero.title}</h1>
              <p className={styles.heroDescription}>{pricesHero.description}</p>
            </div>
          </RevealOnScroll>
        </div>
      </section>

      <section className={styles.plansSection}>
        <div className={styles.container}>
          <div className={styles.plansGrid}>
            {pricePlans.map((plan, index) => (
              <RevealOnScroll
                key={plan.title}
                delay={index * 90}
                className={styles.planReveal}
              >
                <article
                  className={`${styles.planCard} ${
                    plan.featured ? styles.planFeatured : ""
                  }`}
                >
                  {plan.featured ? (
                    <div className={styles.featuredBadge}>{plan.badge}</div>
                  ) : null}
                  {plan.discount ? (
                    <div className={styles.discountBadge}>{plan.discount}</div>
                  ) : null}

                  <div className={styles.planIcon} aria-hidden="true">
                    <PricesIcon name={plan.icon} />
                  </div>
                  <h2 className={styles.planTitle}>{plan.title}</h2>

                  <div className={styles.priceWrap}>
                    <span className={styles.price}>{plan.price}</span>
                    <span className={styles.pricePeriod}>{plan.period}</span>
                    {plan.oldPrice ? (
                      <span className={styles.oldPrice}>{plan.oldPrice}</span>
                    ) : null}
                  </div>

                  {plan.summary ? (
                    <div className={styles.summary}>{plan.summary}</div>
                  ) : null}

                  <ul className={styles.featuresList}>
                    {plan.features.map((feature) => (
                      <li key={feature} className={styles.featureItem}>
                        <span className={styles.featureBullet}>●</span>
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <a href="#" className={styles.selectButton}>
                    Выбрать
                  </a>
                </article>
              </RevealOnScroll>
            ))}
          </div>
        </div>
      </section>

      <section className={styles.compareSection}>
        <div className={styles.container}>
          <RevealOnScroll>
            <div className={styles.compareBox}>
              <h2 className={styles.compareTitle}>Сравни ключевые параметры</h2>
              <div className={styles.compareGrid}>
                {compareItems.map((item) => (
                  <div key={item.title} className={styles.compareItem}>
                    <div className={styles.compareItemTitle}>{item.title}</div>
                    <span className={styles.compareItemValue}>{item.value}</span>
                    <div className={styles.compareItemNote}>{item.note}</div>
                  </div>
                ))}
              </div>
            </div>
          </RevealOnScroll>
        </div>
      </section>

      <section className={styles.faqSection}>
        <div className={styles.container}>
          <RevealOnScroll>
            <>
              <h2 className={styles.faqTitle}>Частые вопросы</h2>
              <Accordion items={pricesFaqItems} />
            </>
          </RevealOnScroll>
        </div>
      </section>

      <section className={styles.ctaSection}>
        <div className={styles.container}>
          <RevealOnScroll>
            <div className={styles.ctaContent}>
              <h2 className={styles.ctaTitle}>{pricesCta.title}</h2>
              <p className={styles.ctaDescription}>{pricesCta.description}</p>
              <a href="#" className={styles.ctaButton}>
                {pricesCta.buttonLabel}
              </a>
            </div>
          </RevealOnScroll>
        </div>
      </section>
    </div>
  );
}
