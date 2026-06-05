export const resourcesHero = {
  title: "Полезные ресурсы",
  description: "Все, что помогает управлять подключением, поддержкой и справочными материалами, собрано в одном месте.",
} as const;

export const quickLinks = [
  { label: "Инструкции", icon: "guide", href: "#" },
  { label: "Бонусы за друзей", icon: "gift", href: "#" },
  { label: "FAQ", icon: "faq", href: "#faq" },
] as const;

export const instructionClients = [
  { label: "Happ", icon: "happ" },
  { label: "v2rayN", icon: "v2rayn" },
  { label: "Nekobox", icon: "nekobox" },
  { label: "Shadowrocket", icon: "shadowrocket" },
] as const;

export const instructionPlatforms = [
  { label: "Windows", icon: "windows" },
  { label: "macOS", icon: "macos" },
  { label: "Android", icon: "android" },
  { label: "iPhone", icon: "iphone" },
] as const;

export const referralBlock = {
  title: "Пригласи друга — получи 7 дней",
  description:
    "За каждого нового пользователя, который активирует платную подписку, вы получаете +7 дней к вашему тарифу.",
  note: "Персональная ссылка появится в кабинете после авторизации и будет доступна в разделе бонусов.",
} as const;

export const myIpBlock = {
  title: "Узнать мой IP",
  description:
    "Проверьте, какой IP сейчас видит сеть. Это удобно перед подключением и после включения маршрута.",
} as const;

export const resourcesFaqItems = [
  {
    title: "Как настроить INFINDA на Windows?",
    content:
      "Достаточно выбрать подходящий клиент, импортировать subscription-ссылку и проверить активный маршрут подключения в кабинете.",
  },
  {
    title: "Что делать, если VPN не подключается?",
    content:
      "Проверь интернет, обнови subscription-ссылку, переключи сервер или обратись в поддержку, если подключение не восстановилось.",
  },
  {
    title: "Как продлить подписку?",
    content:
      "Продление выполняется через личный кабинет: выбери нужный период и подтверди оплату в разделе тарифов.",
  },
  {
    title: "Есть ли ограничение скорости?",
    content:
      "Скорость не режется искусственно. Поведение зависит от выбранного узла, маршрута и текущей сетевой нагрузки.",
  },
  {
    title: "Как связаться с поддержкой?",
    content:
      "Связаться с поддержкой можно через Telegram или email. Если нужен быстрый ответ по подключению или настройке, начните с Telegram.",
  },
] as const;
