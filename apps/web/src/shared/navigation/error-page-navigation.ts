import type { AppRouterInstance } from "next/dist/shared/lib/app-router-context.shared-runtime";

import type { ErrorPageCode } from "@/features/error-page/data/error-content";

export function navigateToErrorPage(
  router: AppRouterInstance,
  code: Exclude<ErrorPageCode, "404"> = "500",
) {
  router.replace(`/${code}`);
}
