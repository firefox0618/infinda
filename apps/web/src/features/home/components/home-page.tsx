import styles from "./home-page.module.css";

import { FeaturesSection } from "./features-section";
import { HeroSection } from "./hero-section";

export function HomePage() {
  return (
    <div className={styles.page}>
      <div className={styles.background} aria-hidden="true" />
      <HeroSection />
      <FeaturesSection />
    </div>
  );
}
