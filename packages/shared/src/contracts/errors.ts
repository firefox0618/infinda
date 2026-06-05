export const apiErrorCodes = {
  apiError: "API_ERROR",
  authenticationFailed: "AUTHENTICATION_FAILED",
  notFound: "NOT_FOUND",
  permissionDenied: "PERMISSION_DENIED",
  validationError: "VALIDATION_ERROR",
} as const;

export type ApiErrorCode =
  (typeof apiErrorCodes)[keyof typeof apiErrorCodes] | string;

export type ApiErrorDto = {
  error: {
    code: ApiErrorCode;
    message: string;
    details: Record<string, unknown>;
  };
};
