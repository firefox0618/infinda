"use client";

import { useState } from "react";

import styles from "./accordion.module.css";

type AccordionItem = {
  title: string;
  content: string;
};

type AccordionProps = {
  items: readonly AccordionItem[];
};

export function Accordion({ items }: AccordionProps) {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  const toggleItem = (index: number) => {
    setOpenIndex((currentIndex) => (currentIndex === index ? null : index));
  };

  return (
    <div className={styles.root}>
      {items.map((item, index) => {
        const isOpen = openIndex === index;

        return (
          <section
            key={item.title}
            className={`${styles.item} ${isOpen ? styles.itemOpen : ""}`}
          >
            <button
              type="button"
              className={styles.trigger}
              aria-expanded={isOpen}
              onClick={() => toggleItem(index)}
            >
              <span>{item.title}</span>
              <span className={styles.chevron} aria-hidden="true">
                ▾
              </span>
            </button>

            <div className={styles.content} hidden={!isOpen}>
              <p className={styles.text}>{item.content}</p>
            </div>
          </section>
        );
      })}
    </div>
  );
}
