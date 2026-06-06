import type { ApiErrorDto } from "@infinda/shared/contracts/errors";

type LegacyErrorPayload = {
  detail?: string;
  email?: string[] | string;
  password?: string[] | string;
  [key: string]: unknown;
};

export type ApiErrorPayload = ApiErrorDto | LegacyErrorPayload | null;
export type ParsedApiError = ApiErrorDto["error"];

export function parseJsonResponse<T>(text: string) {
  if (!text) {
    return null as T | null;
  }

  try {
    return JSON.parse(text) as T;
  } catch {
    return null as T | null;
  }
}

function isWrappedApiError(payload: ApiErrorPayload): payload is ApiErrorDto {
  return Boolean(payload && typeof payload === "object" && "error" in payload);
}

function isLegacyErrorPayload(payload: ApiErrorPayload): payload is LegacyErrorPayload {
  return Boolean(payload && typeof payload === "object" && !("error" in payload));
}

export function extractApiError(payload: ApiErrorPayload): ParsedApiError | null {
  if (!payload) {
    return null;
  }

  if (isWrappedApiError(payload) && payload.error) {
    return payload.error;
  }

  return {
    code: "API_ERROR",
    message:
      isLegacyErrorPayload(payload) && typeof payload.detail === "string"
        ? payload.detail
        : "Request failed.",
    details: isLegacyErrorPayload(payload) ? payload : {},
  };
}
