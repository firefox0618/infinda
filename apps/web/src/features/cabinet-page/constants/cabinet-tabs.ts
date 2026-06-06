import type { CabinetTab } from "../components/cabinet-models";

export const mobileCabinetTabs: { id: CabinetTab; label: string }[] = [
  { id: "overview", label: "Обзор" },
  { id: "subscription", label: "Подписка" },
  { id: "devices", label: "Устройства" },
  { id: "support", label: "Поддержка" },
];

export function resolveCabinetSection(tab: CabinetTab) {
  if (tab === "overview") {
    return { title: "Обзор", subtitle: "Текущая активность и доступ" };
  }

  if (tab === "subscription") {
    return { title: "Подписка", subtitle: "Ссылки, параметры и маршруты" };
  }

  if (tab === "devices") {
    return { title: "Устройства", subtitle: "Контроль подключений и активности" };
  }

  return { title: "Поддержка", subtitle: "Чат и быстрые решения" };
}
