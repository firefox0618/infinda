import Image from "next/image";

import styles from "./hero-section.module.css";

import { RevealOnScroll } from "@/shared/ui/reveal-on-scroll";

export function HeroSection() {
  return (
    <section className={styles.section}>
      <div className={styles.inner}>
        <div className={styles.content}>
          <RevealOnScroll className={styles.logoReveal}>
            <div className={styles.logoWrap}>
              <Image
                className={styles.logo}
                src="/brand/hero-icon.png"
                alt="INFINDA hero icon"
                width={1024}
                height={1024}
                priority
                draggable={false}
              />
            </div>
          </RevealOnScroll>

          <RevealOnScroll delay={70}>
            <div className={styles.eyebrow}>
              <span className={styles.dot} aria-hidden="true" />
              Приватность нового поколения
            </div>
          </RevealOnScroll>

          <RevealOnScroll delay={130}>
            <h1 className={styles.title}>
              Спокойный доступ.
              <br />
              Защищенное подключение.
            </h1>
          </RevealOnScroll>

          <RevealOnScroll delay={190}>
            <p className={styles.subtitle}>
              INFINDA помогает подключаться к сети спокойно: без перегруженного
              интерфейса, без лишних следов и с понятным управлением доступом в
              одном месте.
            </p>
          </RevealOnScroll>

          <RevealOnScroll delay={250}>
            <div className={styles.actions}>
              <a href="#" className={styles.primaryButton}>
                Пробный 3 дня →
              </a>
            </div>
          </RevealOnScroll>

          <RevealOnScroll delay={370}>
            <div className={styles.traffic}>
              Безлимитный трафик на тарифе «12 месяцев»
            </div>
          </RevealOnScroll>
        </div>
      </div>
    </section>
  );
}
