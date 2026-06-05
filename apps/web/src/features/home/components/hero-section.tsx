import Image from "next/image";

import styles from "./hero-section.module.css";

import { RevealOnScroll } from "@/shared/ui/reveal-on-scroll";
import { homeHeroContent } from "../data/home-content";

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
              {homeHeroContent.eyebrow}
            </div>
          </RevealOnScroll>

          <RevealOnScroll delay={130}>
            <h1 className={styles.title}>
              {homeHeroContent.title.split("\n").map((line, index) => (
                <span key={line}>
                  {index > 0 ? <br /> : null}
                  {line}
                </span>
              ))}
            </h1>
          </RevealOnScroll>

          <RevealOnScroll delay={190}>
            <p className={styles.subtitle}>{homeHeroContent.description}</p>
          </RevealOnScroll>

          <RevealOnScroll delay={250}>
            <div className={styles.actions}>
              <a href="#" className={styles.primaryButton}>
                Пробный 3 дня →
              </a>
            </div>
          </RevealOnScroll>

          <RevealOnScroll delay={370}>
            <div className={styles.traffic}>{homeHeroContent.trafficNote}</div>
          </RevealOnScroll>
        </div>
      </div>
    </section>
  );
}
