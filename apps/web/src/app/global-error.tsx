"use client";

import { ErrorPage } from "@/features/error-page/components/error-page";

export default function GlobalErrorPage() {
  return (
    <html lang="en">
      <body>
        <ErrorPage code="500" />
      </body>
    </html>
  );
}
