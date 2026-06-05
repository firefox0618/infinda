"use client";

import { usePathname } from "next/navigation";

import styles from "./site-shell.module.css";

import { SiteFooter } from "./site-footer";
import { SiteHeader } from "./site-header";

type SiteShellProps = {
  children: React.ReactNode;
};

export function SiteShell({ children }: SiteShellProps) {
  const pathname = usePathname();
  const routesWithChrome = new Set([
    "/",
    "/about",
    "/auth",
    "/cabinet",
    "/features",
    "/prices",
    "/resources",
  ]);
  const shouldShowChrome = routesWithChrome.has(pathname);

  return (
    <div className={styles.shell}>
      {shouldShowChrome ? <SiteHeader /> : null}
      <main className={styles.main}>{children}</main>
      {shouldShowChrome ? <SiteFooter /> : null}
    </div>
  );
}
