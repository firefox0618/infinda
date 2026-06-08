import { HappWrapperActions } from "@/features/public-subscription-page/components/happ-wrapper-actions";
import styles from "@/features/public-subscription-page/components/public-subscription-page.module.css";

type HappWrapperPageProps = {
  searchParams: Promise<{
    sub?: string;
  }>;
};

export default async function HappWrapperPage({
  searchParams,
}: HappWrapperPageProps) {
  const params = await searchParams;
  const subscriptionUrl = String(params.sub ?? "").trim();

  if (!subscriptionUrl) {
    return (
      <div className={styles.page}>
        <div className={styles.background} aria-hidden="true" />
        <section className={styles.hero}>
          <p className={styles.eyebrow}>Happ Wrapper</p>
          <h1 className={styles.title}>Ссылка подписки не передана</h1>
          <p className={styles.description}>
            Откройте эту страницу с параметром <code>?sub=...</code>.
          </p>
        </section>
      </div>
    );
  }

  const happDeepLink = `happ://add/${subscriptionUrl}`;

  return (
    <div className={styles.page}>
      <div className={styles.background} aria-hidden="true" />
      <section className={styles.hero}>
        <p className={styles.eyebrow}>Happ Wrapper</p>
        <h1 className={styles.title}>Открыть подписку в Happ</h1>
        <p className={styles.description}>
          Сначала попробуйте открыть Happ напрямую. Если приложение не откроется,
          скопируйте feed и вставьте его в Happ вручную.
        </p>
      </section>

      <section className={styles.routesSection}>
        <div className={styles.routesHeader}>
          <h2 className={styles.routesTitle}>Быстрые действия</h2>
        </div>
        <div className={styles.routesGrid}>
          <article className={styles.routeCard}>
            <div className={styles.routeCountry}>Deep link</div>
            <div className={styles.routeUrlBox}>
              <code className={styles.routeUrlCode}>{happDeepLink}</code>
            </div>
          </article>
          <article className={styles.routeCard}>
            <div className={styles.routeCountry}>Feed ссылка</div>
            <div className={styles.routeUrlBox}>
              <code className={styles.routeUrlCode}>{subscriptionUrl}</code>
            </div>
            <p className={styles.wrapperCardNote}>
              Этот feed можно скопировать ниже и вставить в Happ вручную.
            </p>
          </article>
        </div>
        <HappWrapperActions
          happDeepLink={happDeepLink}
          subscriptionUrl={subscriptionUrl}
        />
      </section>
    </div>
  );
}
