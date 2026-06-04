export const siteNavigationItems = [
  { label: "Главная", href: "#" },
  { label: "Возможности", href: "#features" },
  { label: "Цены", href: "#" },
  { label: "Ресурсы", href: "#" },
  { label: "О нас", href: "#" },
] as const;

export const siteFooterColumns = [
  {
    title: "Навигация",
    links: ["Главная", "Возможности", "Цены", "FAQ", "Инструкции"],
  },
  {
    title: "Ресурсы",
    links: ["Бонусы за друзей", "Status Page", "Мой IP"],
  },
  {
    title: "Правовая",
    links: ["Политики и условия", "Отменить подписку", "Конфиденциальность"],
  },
  {
    title: "О нас",
    links: ["О компании", "Связаться с нами"],
  },
] as const;
