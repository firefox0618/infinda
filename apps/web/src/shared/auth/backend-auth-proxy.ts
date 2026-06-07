import { NextResponse } from "next/server";

import type { ApiErrorDto } from "@infinda/shared/contracts/errors";
import { parseJsonResponse } from "@/shared/api/api-errors";

const DEFAULT_BACKEND_API_BASE_URL = "http://localhost:8000/api/";

function getBackendApiBaseUrl() {
  const configuredBaseUrl =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_BACKEND_API_BASE_URL;

  return configuredBaseUrl.endsWith("/")
    ? configuredBaseUrl
    : `${configuredBaseUrl}/`;
}

function buildBackendUrl(pathname: string) {
  return new URL(pathname, getBackendApiBaseUrl());
}

async function parseBackendBody(response: Response) {
  const text = await response.text();

  if (!text) {
    return null;
  }

  return parseJsonResponse<unknown>(text);
}

function buildInvalidBackendResponse(status: number) {
  const payload: ApiErrorDto = {
    error: {
      code: "UPSTREAM_INVALID_RESPONSE",
      message: "Backend returned an invalid response.",
      details: {
        status,
      },
    },
  };

  return NextResponse.json(payload, { status: 502 });
}

function buildUnavailableBackendResponse() {
  const payload: ApiErrorDto = {
    error: {
      code: "UPSTREAM_UNAVAILABLE",
      message: "Backend is unavailable.",
      details: {},
    },
  };

  return NextResponse.json(payload, { status: 502 });
}

export async function proxyBackendAuthRequest(options: {
  pathname: string;
  method: "GET" | "POST" | "PATCH" | "DELETE";
  authorization?: string | null;
  body?: unknown;
}) {
  const headers = new Headers();

  if (options.authorization) {
    headers.set("Authorization", options.authorization);
  }

  if (options.body !== undefined) {
    headers.set("Content-Type", "application/json");
  }

  let response: Response;
  try {
    response = await fetch(buildBackendUrl(options.pathname), {
      method: options.method,
      headers,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
      cache: "no-store",
    });
  } catch {
    return buildUnavailableBackendResponse();
  }

  if (response.status === 204) {
    return new NextResponse(null, { status: response.status });
  }

  const payload = await parseBackendBody(response);

  if (payload === null && response.status !== 204) {
    return buildInvalidBackendResponse(response.status);
  }

  return NextResponse.json(payload, { status: response.status });
}

export async function proxyBackendMultipartRequest(options: {
  pathname: string;
  method: "POST";
  authorization?: string | null;
  body: FormData;
}) {
  const headers = new Headers();

  if (options.authorization) {
    headers.set("Authorization", options.authorization);
  }

  let response: Response;
  try {
    response = await fetch(buildBackendUrl(options.pathname), {
      method: options.method,
      headers,
      body: options.body,
      cache: "no-store",
    });
  } catch {
    return buildUnavailableBackendResponse();
  }

  const payload = await parseBackendBody(response);

  if (payload === null && response.status !== 204) {
    return buildInvalidBackendResponse(response.status);
  }

  return NextResponse.json(payload, { status: response.status });
}
