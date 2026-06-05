export const cabinetOverviewStats = [
  { title: "Осталось дней", value: "365", note: "подписка активна" },
  { title: "Использовано трафика", value: "247 ГБ", note: "без лимита" },
  { title: "Активные устройства", value: "0", note: "из 10 доступных" },
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
