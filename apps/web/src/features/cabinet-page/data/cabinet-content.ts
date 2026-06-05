export const cabinetOverviewStats = [
  { title: "Осталось дней", value: "365", note: "подписка активна" },
  { title: "Использовано трафика", value: "247 ГБ", note: "без лимита" },
  { title: "Активные устройства", value: "2", note: "из 10 доступных" },
] as const;

export const cabinetTrafficWeek = [
  { label: "Пн", value: 42 },
  { label: "Вт", value: 35 },
  { label: "Ср", value: 48 },
  { label: "Чт", value: 30 },
  { label: "Пт", value: 54 },
  { label: "Сб", value: 40 },
  { label: "Вс", value: 46 },
] as const;

export const cabinetSubscriptionLinks = {
  main: "https://infinda.com/sub/abc123xyz",
  countries: [
    { code: "ru", label: "Россия", url: "https://infinda.com/sub/ru-abc123xyz" },
    { code: "ee", label: "Эстония", url: "https://infinda.com/sub/ee-abc123xyz" },
    { code: "de", label: "Германия", url: "https://infinda.com/sub/de-abc123xyz" },
    { code: "nl", label: "Нидерланды", url: "https://infinda.com/sub/nl-abc123xyz" },
  ],
} as const;

export const cabinetSubscriptionDetails = [
  { label: "Тариф", value: "12 месяцев (безлимит)" },
  { label: "Активна до", value: "4 июня 2027" },
  { label: "Осталось дней", value: "365" },
  { label: "Устройств", value: "5 из 10" },
] as const;

export const cabinetDevices = [
  {
    name: "Windows PC",
    icon: "desktop",
    ip: "192.168.1.101",
    lastSeen: "Сегодня 14:23",
    status: "online",
    meta: "Windows 11 · Chrome 125",
  },
  {
    name: "iPhone 14 Pro",
    icon: "mobile",
    ip: "192.168.1.105",
    lastSeen: "Сегодня 12:15",
    status: "online",
    meta: "iOS 17.5 · Safari",
  },
  {
    name: "MacBook Air",
    icon: "laptop",
    ip: "192.168.1.110",
    lastSeen: "Вчера 22:10",
    status: "offline",
    meta: "macOS 14.5 · Firefox",
  },
] as const;

export const cabinetMessages = [
  {
    id: "support-1",
    author: "Анна (поддержка)",
    side: "support",
    text: "Здравствуйте. Чем можем помочь по вашей подписке?",
  },
  {
    id: "user-1",
    author: "Вы",
    side: "user",
    text: "Подскажите, как выбрать отдельную ссылку под конкретную страну?",
  },
  {
    id: "support-2",
    author: "Дмитрий (поддержка)",
    side: "support",
    text: "Откройте вкладку «Подписка», выберите страну и скопируйте готовую ссылку на сервер.",
  },
] as const;
