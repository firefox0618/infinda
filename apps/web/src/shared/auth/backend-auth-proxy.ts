import { NextResponse } from "next/server";

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

  return JSON.parse(text);
}

export async function proxyBackendAuthRequest(options: {
  pathname: string;
  method: "GET" | "POST" | "PATCH";
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

  const response = await fetch(buildBackendUrl(options.pathname), {
    method: options.method,
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    cache: "no-store",
  });

  if (response.status === 204) {
    return new NextResponse(null, { status: response.status });
  }

  const payload = await parseBackendBody(response);
  return NextResponse.json(payload, { status: response.status });
}
