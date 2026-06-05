export type ResourcesIconName =
  | "guide"
  | "gift"
  | "faq"
  | "happ"
  | "v2rayn"
  | "nekobox"
  | "shadowrocket"
  | "windows"
  | "macos"
  | "android"
  | "iphone";

type ResourcesIconProps = {
  name: ResourcesIconName;
};

export function ResourcesIcon({ name }: ResourcesIconProps) {
  switch (name) {
    case "guide":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <rect x="4" y="4" width="16" height="16" rx="3.5" stroke="currentColor" strokeWidth="1.8" />
          <path d="M8 8.5h8M8 12h5.5M8 15.5h4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
          <path d="M15.8 16.2 18.5 18.8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
          <circle cx="14.2" cy="14.5" r="2.3" stroke="currentColor" strokeWidth="1.8" />
        </svg>
      );
    case "gift":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M4 10h16v10H4zM12 10v10M3 7.5h18V10H3z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
          <path d="M12 7.5c0-2 1.2-3.5 3-3.5 1.2 0 2 .8 2 1.9 0 2-2.3 2.9-5 3.6ZM12 7.5c0-2-1.2-3.5-3-3.5-1.2 0-2 .8-2 1.9 0 2 2.3 2.9 5 3.6Z" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "faq":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M12 18h.01M9.1 9a3 3 0 1 1 5.6 1.5c-.9 1-1.7 1.5-1.7 2.8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
          <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.8" />
        </svg>
      );
    case "happ":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <rect x="4" y="4" width="16" height="16" rx="4" stroke="currentColor" strokeWidth="1.8" />
          <path d="M9 8v8M15 8v8M9 12h6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
    case "v2rayn":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M5 7.5 9.2 16 13.4 7.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M14.8 16V8l4.2 8V8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "nekobox":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M7 9 9.2 6l2 2M17 9 14.8 6l-2 2" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
          <rect x="5" y="8" width="14" height="11" rx="4" stroke="currentColor" strokeWidth="1.8" />
          <path d="M10 13h.01M14 13h.01M10 16c.8.7 1.5 1 2 1s1.2-.3 2-1" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
    case "shadowrocket":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M14.5 5.5c2.7.7 4.3 3.5 3.6 6.2-.2.8-.7 1.6-1.3 2.2l-5.6 5.6-2.8.8.8-2.8 5.6-5.6c.6-.6 1.3-1 2.2-1.3" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
          <path d="M13 8.5 15.5 11M8.5 15.5l-1.7 1.7" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
    case "windows":
      return (
        <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
          <path d="M3 5.4 10.5 4v7H3V5.4ZM12 3.8 21 2.5V11h-9V3.8ZM3 12.8h7.5v7L3 18.6v-5.8ZM12 12.8h9v8.7l-9-1.3v-7.4Z" />
        </svg>
      );
    case "macos":
    case "iphone":
      return (
        <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
          <path d="M16.7 12.8c0-2.2 1.8-3.3 1.9-3.4-1-1.5-2.7-1.7-3.3-1.7-1.4-.1-2.7.8-3.4.8-.7 0-1.8-.8-3-.8-1.5 0-3 .9-3.8 2.3-1.6 2.7-.4 6.7 1.1 8.9.7 1.1 1.6 2.3 2.8 2.3 1.1 0 1.6-.7 3-.7 1.4 0 1.8.7 3 .7 1.2 0 2-.9 2.7-2 .8-1.1 1.1-2.2 1.1-2.2-.1 0-2.1-.8-2.1-4.2ZM14.4 6.3c.6-.7 1.1-1.7 1-2.7-.9 0-2 .6-2.6 1.3-.6.6-1.1 1.7-.9 2.6 1 .1 1.9-.5 2.5-1.2Z" />
        </svg>
      );
    case "android":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M8 9.5h8a2 2 0 0 1 2 2V17a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2v-5.5a2 2 0 0 1 2-2Z" stroke="currentColor" strokeWidth="1.8" />
          <path d="M9 9a3 3 0 0 1 6 0M9.5 5.5 8 3.8M14.5 5.5 16 3.8M9.5 13h.01M14.5 13h.01" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
  }
}
