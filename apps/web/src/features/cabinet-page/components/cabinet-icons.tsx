import type { ReactNode } from "react";

import type { CabinetTab } from "./cabinet-types";

function iconPath(children: ReactNode) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      {children}
    </svg>
  );
}

const strokeProps = {
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.85,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

export function CabinetNavIcon({ tab }: { tab: CabinetTab }) {
  if (tab === "overview") {
    return iconPath(
      <>
        <path {...strokeProps} d="M4.5 11.5 12 5l7.5 6.5" />
        <path {...strokeProps} d="M6.5 10.5V19h11v-8.5" />
      </>,
    );
  }

  if (tab === "subscription") {
    return iconPath(
      <>
        <rect {...strokeProps} x="4" y="6" width="16" height="12" rx="3" />
        <path {...strokeProps} d="M7.5 10h9M7.5 14h5.5" />
      </>,
    );
  }

  if (tab === "devices") {
    return iconPath(
      <>
        <rect {...strokeProps} x="4" y="5" width="16" height="10.5" rx="2.4" />
        <path {...strokeProps} d="M9 19h6M12 15.5V19" />
      </>,
    );
  }

  return iconPath(
    <>
      <path {...strokeProps} d="M6 8h12M6 12h8M6 16h10" />
      <path {...strokeProps} d="M18 8h.01M16 12h.01M18 16h.01" />
    </>,
  );
}

export function LogoutIcon() {
  return iconPath(
    <path
      {...strokeProps}
      d="M14 7l5 5-5 5M19 12H9M11 5H7a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h4"
    />,
  );
}

export function DeviceIcon({
  kind,
}: {
  kind: "desktop" | "mobile" | "laptop";
}) {
  if (kind === "mobile") {
    return iconPath(
      <>
        <rect {...strokeProps} x="8" y="3.5" width="8" height="17" rx="2.5" />
        <path {...strokeProps} d="M11 6.5h2M11.5 17.5h1" />
      </>,
    );
  }

  if (kind === "laptop") {
    return iconPath(
      <>
        <rect {...strokeProps} x="5" y="5" width="14" height="9" rx="1.8" />
        <path {...strokeProps} d="M3.5 18h17" />
      </>,
    );
  }

  return iconPath(
    <>
      <rect {...strokeProps} x="4" y="4.5" width="16" height="10.5" rx="2.3" />
      <path {...strokeProps} d="M9 19h6M12 15V19" />
    </>,
  );
}

export function CopyIcon() {
  return iconPath(
    <>
      <rect {...strokeProps} x="9" y="7" width="10" height="12" rx="2.2" />
      <path {...strokeProps} d="M15 7V6a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h2" />
    </>,
  );
}

export function SparkIcon() {
  return iconPath(
    <>
      <path {...strokeProps} d="m12 4 1.6 4.4L18 10l-4.4 1.6L12 16l-1.6-4.4L6 10l4.4-1.6Z" />
    </>,
  );
}

export function SupportPulseIcon() {
  return iconPath(
    <>
      <circle {...strokeProps} cx="12" cy="12" r="4.8" />
      <path {...strokeProps} d="M12 3.8v1.2M12 19v1.2M4.8 12H3.6M20.4 12h-1.2" />
    </>,
  );
}

export function AttachIcon() {
  return iconPath(
    <path
      {...strokeProps}
      d="M9.5 12.5 15 7a3 3 0 1 1 4.2 4.2l-7.1 7.1a5 5 0 1 1-7.1-7.1l7.4-7.4"
    />,
  );
}
