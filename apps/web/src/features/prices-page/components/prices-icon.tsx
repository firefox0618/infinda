type PricesIconName = "feather" | "calendar" | "semester" | "crown";

type PricesIconProps = {
  name: PricesIconName;
};

export function PricesIcon({ name }: PricesIconProps) {
  switch (name) {
    case "feather":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="M19 5.5c-4.8 0-8.1 2.8-10.4 7.1-1 1.9-1.7 3.9-2.1 6.2 2.3-.4 4.3-1.1 6.2-2.1C17 14.4 19.8 11 19 5.5Z"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinejoin="round"
          />
          <path d="M8.5 15.5 15.5 8.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
    case "calendar":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <rect x="4" y="5" width="16" height="15" rx="3" stroke="currentColor" strokeWidth="1.8" />
          <path d="M8 3.8v3.4M16 3.8v3.4M4 9h16" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
    case "semester":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="M6 5.5h9.5a2.5 2.5 0 0 1 2.5 2.5v10.5H8.5A2.5 2.5 0 0 0 6 21V5.5Z"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinejoin="round"
          />
          <path d="M8.4 9.2h6.4M8.4 12.2h6.4M8.4 15.2h4.3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
    case "crown":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="m4 8 4.2 4.4L12 6.5l3.8 5.9L20 8l-1.6 9H5.6L4 8Z"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinejoin="round"
          />
          <path d="M7 18.5h10" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
  }
}
