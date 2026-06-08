import { NextResponse } from "next/server";

import { publicSubscriptionApiPaths } from "@infinda/shared/contracts/public-subscription";
import { parseJsonResponse } from "@/shared/api/api-errors";

const DEFAULT_BACKEND_API_BASE_URL = "http://localhost:8000/api/";

function getBackendApiBaseUrl() {
  const configuredBaseUrl =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_BACKEND_API_BASE_URL;

  return configuredBaseUrl.endsWith("/")
    ? configuredBaseUrl
    : `${configuredBaseUrl}/`;
}

type RouteContext = {
  params: Promise<{
    token: string;
  }>;
};

export async function POST(request: Request, context: RouteContext) {
  const { token } = await context.params;
  const rawBody = await request.text();

  const headers = new Headers();
  headers.set("Content-Type", "application/json");
  const forwardedFor = request.headers.get("x-forwarded-for");
  if (forwardedFor) {
    headers.set("X-Forwarded-For", forwardedFor);
  }
  const realIp = request.headers.get("x-real-ip");
  if (realIp) {
    headers.set("X-Real-IP", realIp);
  }
  const deviceKey = request.headers.get("x-device-key");
  if (deviceKey) {
    headers.set("X-Device-Key", deviceKey);
  }
  const userAgent = request.headers.get("user-agent");
  if (userAgent) {
    headers.set("User-Agent", userAgent);
  }

  let response: Response;
  try {
    response = await fetch(
      new URL(publicSubscriptionApiPaths.touch(token), getBackendApiBaseUrl()),
      {
        method: "POST",
        headers,
        body: rawBody || "{}",
        cache: "no-store",
      },
    );
  } catch {
    return NextResponse.json(
      {
        error: {
          code: "UPSTREAM_UNAVAILABLE",
          message: "Backend is unavailable.",
          details: {},
        },
      },
      { status: 502 },
    );
  }

  const text = await response.text();
  if (!text) {
    return NextResponse.json(
      {
        error: {
          code: "UPSTREAM_INVALID_RESPONSE",
          message: "Backend returned an invalid response.",
          details: {
            status: response.status,
          },
        },
      },
      { status: 502 },
    );
  }

  return NextResponse.json(parseJsonResponse<unknown>(text), { status: response.status });
}
