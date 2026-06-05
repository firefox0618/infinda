type AboutIconName =
  | "shield"
  | "bolt"
  | "support"
  | "astronaut"
  | "product"
  | "database"
  | "globe"
  | "chart"
  | "branch"
  | "speed"
  | "telegram"
  | "mail"
  | "ticket";

type AboutIconProps = {
  name: AboutIconName;
};

export function AboutIcon({ name }: AboutIconProps) {
  const commonProps = {
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
  };

  switch (name) {
    case "shield":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path {...commonProps} d="M12 3l7 3v5c0 4.5-2.8 7.8-7 10-4.2-2.2-7-5.5-7-10V6l7-3z" />
        </svg>
      );
    case "bolt":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path {...commonProps} d="M13 2L5 14h6l-1 8 9-13h-6l0-7z" />
        </svg>
      );
    case "support":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path {...commonProps} d="M4 13v-1a8 8 0 0116 0v1" />
          <path {...commonProps} d="M4 13v3a2 2 0 002 2h1v-5H6a2 2 0 00-2 2z" />
          <path {...commonProps} d="M20 13v3a2 2 0 01-2 2h-1v-5h1a2 2 0 012 2z" />
          <path {...commonProps} d="M9 19.5a6.5 6.5 0 006 0" />
        </svg>
      );
    case "astronaut":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle {...commonProps} cx="12" cy="8" r="4" />
          <path {...commonProps} d="M6 21c0-3.3 2.7-6 6-6s6 2.7 6 6" />
        </svg>
      );
    case "product":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <rect {...commonProps} x="4" y="4" width="16" height="16" rx="3" />
          <path {...commonProps} d="M8 8h8M8 12h5M8 16h8" />
        </svg>
      );
    case "database":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <ellipse {...commonProps} cx="12" cy="6" rx="7" ry="3" />
          <path {...commonProps} d="M5 6v6c0 1.7 3.1 3 7 3s7-1.3 7-3V6" />
          <path {...commonProps} d="M5 12v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6" />
        </svg>
      );
    case "globe":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle {...commonProps} cx="12" cy="12" r="9" />
          <path {...commonProps} d="M3 12h18M12 3a14 14 0 010 18M12 3a14 14 0 000 18" />
        </svg>
      );
    case "chart":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path {...commonProps} d="M4 19h16" />
          <path {...commonProps} d="M7 15l3-3 3 2 4-5" />
          <circle cx="7" cy="15" r="1.2" fill="currentColor" />
          <circle cx="10" cy="12" r="1.2" fill="currentColor" />
          <circle cx="13" cy="14" r="1.2" fill="currentColor" />
          <circle cx="17" cy="9" r="1.2" fill="currentColor" />
        </svg>
      );
    case "branch":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle {...commonProps} cx="7" cy="6" r="2.5" />
          <circle {...commonProps} cx="17" cy="6" r="2.5" />
          <circle {...commonProps} cx="17" cy="18" r="2.5" />
          <path {...commonProps} d="M9.5 6H14a3 3 0 013 3v6" />
        </svg>
      );
    case "speed":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path {...commonProps} d="M5 16a8 8 0 1114 0" />
          <path {...commonProps} d="M12 12l4-3" />
          <path {...commonProps} d="M8 18h8" />
        </svg>
      );
    case "telegram":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path {...commonProps} d="M21 4L3 11l5.5 2 2 6L21 4z" />
          <path {...commonProps} d="M8.5 13l7-5.5" />
        </svg>
      );
    case "mail":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <rect {...commonProps} x="3" y="5" width="18" height="14" rx="3" />
          <path {...commonProps} d="M5 8l7 5 7-5" />
        </svg>
      );
    case "ticket":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path {...commonProps} d="M4 7a2 2 0 012-2h12a2 2 0 012 2v3a2 2 0 010 4v3a2 2 0 01-2 2H6a2 2 0 01-2-2v-3a2 2 0 010-4V7z" />
          <path {...commonProps} d="M12 7v10" />
        </svg>
      );
  }
}
