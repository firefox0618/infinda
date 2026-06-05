type FeaturesIconName =
  | "shield"
  | "routing"
  | "ban"
  | "devices"
  | "dashboard"
  | "support";

type FeaturesIconProps = {
  name: FeaturesIconName;
};

export function FeaturesIcon({ name }: FeaturesIconProps) {
  switch (name) {
    case "shield":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="M12 2.5 5.5 5v6.2c0 4.27 2.68 8.13 6.5 9.55 3.82-1.42 6.5-5.28 6.5-9.55V5L12 2.5Z"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinejoin="round"
          />
          <path
            d="m9.3 12.1 1.7 1.7 3.8-3.9"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      );
    case "routing":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle cx="6" cy="7" r="2.2" fill="currentColor" />
          <circle cx="18" cy="6" r="2.2" fill="currentColor" />
          <circle cx="12" cy="18" r="2.2" fill="currentColor" />
          <path
            d="M7.9 7.5h7.7M7.6 8.8l2.9 6.4m5-8.1-2.8 6.1"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
        </svg>
      );
    case "ban":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle cx="12" cy="12" r="8.5" stroke="currentColor" strokeWidth="1.8" />
          <path
            d="m8.2 15.8 7.6-7.6"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
        </svg>
      );
    case "devices":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <rect x="4" y="5" width="10" height="13" rx="2" stroke="currentColor" strokeWidth="1.8" />
          <path d="M17 9h3v8h-8v-3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
          <path d="M8.5 15h1" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
    case "dashboard":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="M5 18.5V13m5 5.5V9m5 9.5V5m4 13.5H3"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      );
    case "support":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="M6.6 15.6a7 7 0 1 1 10.8 0M8.3 17.2c0 1 .8 1.8 1.8 1.8h3.8c1 0 1.8-.8 1.8-1.8"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
          <path
            d="M9.8 13.2h.1m4.2 0h.1"
            stroke="currentColor"
            strokeWidth="2.2"
            strokeLinecap="round"
          />
        </svg>
      );
  }
}
