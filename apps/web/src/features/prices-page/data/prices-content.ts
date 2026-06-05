type PricePlan = {
  code: "1m" | "3m" | "6m" | "12m";
  icon: "feather" | "calendar" | "semester" | "crown";
  title: string;
  price: string;
  period: string;
  summary: string;
  features: string[];
  oldPrice?: string;
  discount?: string;
  featured?: boolean;
  badge?: string;
};

export const pricesHero = {
  title: "Выберите подходящий тариф",
  description:
    "Попробуйте INFINDA на короткий срок или оформите подписку надолго — чем больше период, тем выгоднее доступ.",
} as const;

export const pricePlans: PricePlan[] = [
  {
    code: "1m",
    icon: "feather",
    title: "1 месяц",
    price: "149 ₽",
    period: "",
    summary: "",
    features: ["45 ГБ трафика", "3 устройства", "4 страны", "Контроль подключений"],
  },
  {
    code: "3m",
    icon: "calendar",
    title: "3 месяца",
    price: "399 ₽",
    period: "",
    oldPrice: "447 ₽",
    discount: "−10%",
    summary: "",
    features: ["70 ГБ/мес", "4 устройства", "Приоритетная поддержка", "Все серверы"],
  },
  {
    code: "6m",
    icon: "semester",
    title: "6 месяцев",
    price: "749 ₽",
    period: "",
    oldPrice: "880 ₽",
    discount: "−15%",
    summary: "",
    features: ["100 ГБ/мес", "5 устройств", "Приоритетная поддержка", "Все серверы"],
  },
  {
    code: "12m",
    icon: "crown",
    title: "12 месяцев",
    price: "1 390 ₽",
    period: "",
    oldPrice: "1 788 ₽",
    discount: "−20%",
    summary: "",
    features: [
      "Безлимитный трафик",
      "До 10 устройств",
      "Эксклюзивные серверы (скоро)",
      "Приоритет 24/7",
    ],
    featured: true,
    badge: "Best value",
  },
] as const;

export const compareItems = [
  { title: "Скорость", value: "до 1 ГБит/с", note: "на всех тарифах" },
  { title: "Серверы", value: "4 страны", note: "RU, EE, DE, NL" },
  { title: "Шифрование", value: "256‑бит", note: "AES" },
  { title: "Пробный доступ", value: "3 дня", note: "без оплаты" },
] as const;

export const pricesFaqItems = [
  { title: "Можно ли сменить тариф?", content: "Да, в личном кабинете можно продлить или выбрать новый сценарий подписки в любой момент." },
  { title: "Что такое безлимитный трафик?", content: "На годовом тарифе трафик не ограничивается, поэтому можно не следить за остатками и работать в спокойном режиме." },
  { title: "Как получить пробные 3 дня?", content: "Пробный период активируется после регистрации. Это удобный способ проверить подключение и кабинет до оплаты." },
  { title: "Какие способы оплаты доступны?", content: "Банковские карты, СБП и другие способы оплаты будут подключаться по мере развития продуктового контура." },
] as const;

export const pricesCta = {
  title: "Попробуйте перед подпиской",
  description:
    "Оформите пробный доступ и проверьте INFINDA в реальной работе: подключение, кабинет и управление устройствами.",
  buttonLabel: "Начать 3 дня бесплатно →",
} as const;
