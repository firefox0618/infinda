export const siteNavigationItems = [
  { label: "Главная", href: "/" },
  { label: "Возможности", href: "/features" },
  { label: "Цены", href: "/prices" },
  { label: "Ресурсы", href: "/resources" },
  { label: "О нас", href: "/about" },
] as const;

export const siteFooterColumns = [
  {
    title: "Навигация",
    links: [
      { label: "Главная", href: "/" },
      { label: "Возможности", href: "/features" },
      { label: "Цены", href: "/prices" },
      { label: "Ресурсы", href: "/resources" },
    ],
  },
  {
    title: "Ресурсы",
    links: [
      { label: "Бонусы за друзей", href: "/resources" },
      { label: "Статус серверов", href: "/resources" },
      { label: "Мой IP", href: "/resources" },
    ],
  },
  {
    title: "Правовая",
    links: [
      { label: "Политики и условия", href: "/auth" },
      { label: "Отменить подписку", href: "/cabinet" },
      { label: "Конфиденциальность", href: "/about" },
    ],
  },
  {
    title: "О нас",
    links: [
      { label: "О компании", href: "/about" },
      { label: "Связаться с нами", href: "/about" },
      { label: "Личный кабинет", href: "/cabinet" },
    ],
  },
] as const;
