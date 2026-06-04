"use client";

import { useEffect, useRef, useState } from "react";

import styles from "./reveal-on-scroll.module.css";

type RevealOnScrollProps = {
  children: React.ReactNode;
  className?: string;
  delay?: number;
};

export function RevealOnScroll({
  children,
  className,
  delay = 0,
}: RevealOnScrollProps) {
  const [isVisible, setIsVisible] = useState(false);
  const elementRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const node = elementRef.current;

    if (!node) {
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) {
          return;
        }

        setIsVisible(true);
        observer.disconnect();
      },
      {
        rootMargin: "0px 0px -10% 0px",
        threshold: 0.15,
      },
    );

    observer.observe(node);

    return () => {
      observer.disconnect();
    };
  }, []);

  const resolvedClassName = [styles.reveal, isVisible ? styles.visible : "", className]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      ref={elementRef}
      className={resolvedClassName}
      style={{ transitionDelay: `${delay}ms` }}
    >
      {children}
    </div>
  );
}
