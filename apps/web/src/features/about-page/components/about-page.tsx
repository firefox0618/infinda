import Link from "next/link";

import { RevealOnScroll } from "@/shared/ui/reveal-on-scroll";

import styles from "./about-page.module.css";

import { AboutIcon } from "./about-icon";
import { AnimatedStat } from "./animated-stat";
import { ContactCopyButton } from "./contact-copy-button";
import {
  aboutContacts,
  aboutFacts,
  aboutHero,
  aboutMission,
  aboutStats,
  aboutTeam,
  aboutValues,
} from "../data/about-content";

export function AboutPage() {
  return (
    <div className={styles.page}>
      <div className={styles.background} aria-hidden="true" />
      <div className={styles.container}>
        <RevealOnScroll>
          <section className={styles.hero}>
            <span className={styles.eyebrow}>О компании</span>
            <h1 className={styles.title}>{aboutHero.title}</h1>
            <p className={styles.description}>{aboutHero.description}</p>
          </section>
        </RevealOnScroll>

        <RevealOnScroll>
          <section className={styles.missionCard}>
            <h2>{aboutMission.title}</h2>
            <p>{aboutMission.description}</p>
          </section>
        </RevealOnScroll>

        <RevealOnScroll>
          <section className={styles.statsGrid}>
            {aboutStats.map((stat) => (
              <article key={stat.label} className={styles.statCard}>
                <div className={styles.statValue}>
                  <AnimatedStat value={stat.value} />
                </div>
                <div className={styles.statLabel}>{stat.label}</div>
              </article>
            ))}
          </section>
        </RevealOnScroll>

        <RevealOnScroll>
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Наши ценности</h2>
            <div className={styles.valueGrid}>
              {aboutValues.map((value) => (
                <article key={value.title} className={styles.valueCard}>
                  <div className={styles.iconWrap}>
                    <AboutIcon name={value.icon} />
                  </div>
                  <h3>{value.title}</h3>
                  <p>{value.description}</p>
                </article>
              ))}
            </div>
          </section>
        </RevealOnScroll>

        <RevealOnScroll>
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Команда</h2>
            <div className={styles.teamGrid}>
              {aboutTeam.map((member) => (
                <article key={member.role} className={styles.teamCard}>
                  <div className={styles.avatarWrap}>
                    <AboutIcon name={member.icon} />
                  </div>
                  <h3>{member.role}</h3>
                  <span className={styles.teamRole}>Основатель</span>
                  <p>{member.bio}</p>
                </article>
              ))}
            </div>
          </section>
        </RevealOnScroll>

        <RevealOnScroll>
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Интересные факты</h2>
            <div className={styles.factGrid}>
              {aboutFacts.map((fact) => (
                <article key={fact.title} className={styles.factCard}>
                  <div className={styles.factTitle}>
                    <AboutIcon name={fact.icon} />
                    <h3>{fact.title}</h3>
                  </div>
                  <p>{fact.description}</p>
                </article>
              ))}
            </div>
          </section>
        </RevealOnScroll>

        <RevealOnScroll>
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Свяжитесь с нами</h2>
            <div className={styles.contactGrid}>
              {aboutContacts.map((contact) => (
                <article key={contact.title} className={styles.contactCard}>
                  <div className={styles.iconWrap}>
                    <AboutIcon name={contact.icon} />
                  </div>
                  <h3>{contact.title}</h3>
                  <Link
                    href={contact.href}
                    className={styles.contactLink}
                    target={contact.href.startsWith("http") ? "_blank" : undefined}
                  >
                    {contact.value}
                  </Link>
                  <ContactCopyButton value={contact.copyValue} />
                </article>
              ))}
            </div>
          </section>
        </RevealOnScroll>

        <RevealOnScroll>
          <section className={styles.cta}>
            <h2>Присоединяйся к INFINDA</h2>
            <p>
              Начни с пробного периода, чтобы проверить скорость, маршрутизацию
              и интерфейс в своем собственном ритме.
            </p>
            <Link href="/auth" className={styles.ctaButton}>
              Начать 3 дня бесплатно
            </Link>
          </section>
        </RevealOnScroll>
      </div>
    </div>
  );
}
