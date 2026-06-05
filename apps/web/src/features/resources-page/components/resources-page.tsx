import styles from "./resources-page.module.css";

import { Accordion } from "@/shared/ui/accordion";
import { RevealOnScroll } from "@/shared/ui/reveal-on-scroll";

import {
  instructionClients,
  instructionPlatforms,
  myIpBlock,
  quickLinks,
  referralBlock,
  resourcesFaqItems,
  resourcesHero,
} from "../data/resources-content";
import { InstructionSelector } from "./instruction-selector";
import { MyIpCard } from "./my-ip-card";
import { ResourcesIcon } from "./resources-icon";

export function ResourcesPage() {
  return (
    <div className={styles.page}>
      <div className={styles.background} aria-hidden="true" />

      <section className={styles.heroSection}>
        <div className={styles.container}>
          <RevealOnScroll>
            <div className={styles.heroContent}>
              <h1 className={styles.heroTitle}>{resourcesHero.title}</h1>
              <p className={styles.heroDescription}>{resourcesHero.description}</p>
            </div>
          </RevealOnScroll>
        </div>
      </section>

      <section className={styles.linksSection}>
        <div className={styles.container}>
          <RevealOnScroll>
            <div className={styles.linksRow}>
              {quickLinks.map((link) => (
                <a key={link.label} href={link.href} className={styles.quickLink}>
                  <span className={styles.quickLinkIcon}>
                    <ResourcesIcon name={link.icon} />
                  </span>
                  <span>{link.label}</span>
                </a>
              ))}
            </div>
          </RevealOnScroll>
        </div>
      </section>

      <section className={styles.columnsSection}>
        <div className={styles.container}>
          <div className={styles.columns}>
            <RevealOnScroll>
              <div className={`${styles.glassCard} ${styles.instructionCard}`}>
                <h2 className={styles.cardTitle}>
                  <span className={styles.cardTitleMark} aria-hidden="true">
                    <ResourcesIcon name="guide" />
                  </span>
                  Инструкции
                </h2>
                <p className={styles.cardDescription}>
                  Выберите клиент и подходящую операционную систему. Дальше на
                  этом месте можно будет открыть точную инструкцию для нужного
                  сценария подключения.
                </p>
                <InstructionSelector
                  clients={instructionClients}
                  platforms={instructionPlatforms}
                />
              </div>
            </RevealOnScroll>

            <RevealOnScroll delay={80}>
              <div className={styles.sideStack}>
                <div className={styles.glassCard}>
                  <h2 className={styles.cardTitle}>
                    <span
                      className={`${styles.cardTitleMark} ${styles.cardTitleMarkPulse}`}
                      aria-hidden="true"
                    >
                      <span className={styles.onlineDot} />
                    </span>
                    {myIpBlock.title}
                  </h2>
                  <p className={styles.cardDescription}>{myIpBlock.description}</p>
                  <MyIpCard />
                </div>

                <div className={`${styles.glassCard} ${styles.referralCard}`}>
                  <h2 className={styles.cardTitle}>
                    <span className={styles.cardTitleMark} aria-hidden="true">
                      <ResourcesIcon name="gift" />
                    </span>
                    Реферальная программа
                  </h2>

                  <div className={styles.referralBlock}>
                    <div className={styles.referralHead}>
                      <span className={styles.referralIcon}>✦</span>
                      <div className={styles.referralTitle}>{referralBlock.title}</div>
                    </div>
                    <p className={styles.referralDescription}>
                      {referralBlock.description}
                    </p>
                    <p className={styles.referralNote}>{referralBlock.note}</p>
                  </div>
                </div>
              </div>
            </RevealOnScroll>
          </div>
        </div>
      </section>

      <section className={styles.faqSection} id="faq">
        <div className={styles.container}>
          <RevealOnScroll>
            <>
              <h2 className={styles.faqTitle}>Частые вопросы</h2>
              <Accordion items={resourcesFaqItems} />
            </>
          </RevealOnScroll>
        </div>
      </section>
    </div>
  );
}
