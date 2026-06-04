type FeatureIconName = "shield" | "bolt" | "unlock";

type FeatureIconProps = {
  name: FeatureIconName;
};

export function FeatureIcon({ name }: FeatureIconProps) {
  if (name === "shield") {
    return (
      <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M12 2.5 5.5 5v6.2c0 4.27 2.68 8.13 6.5 9.55 3.82-1.42 6.5-5.28 6.5-9.55V5L12 2.5Z"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinejoin="round"
        />
        <path
          d="m9.2 11.9 1.9 1.9 3.7-4"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    );
  }

  if (name === "bolt") {
    return (
      <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M13.4 2.5 6.8 13h4.5l-1 8.5L17.2 11h-4.4l.6-8.5Z"
          fill="currentColor"
        />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect
        x="4"
        y="10"
        width="16"
        height="10"
        rx="3"
        stroke="currentColor"
        strokeWidth="1.8"
      />
      <path
        d="M8 10V7.8A4 4 0 0 1 12 4a4 4 0 0 1 4 3.8V10"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
      <circle cx="12" cy="15" r="1.2" fill="currentColor" />
    </svg>
  );
}
