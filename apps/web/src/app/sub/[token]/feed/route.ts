import { publicSubscriptionApiPaths } from "@infinda/shared/contracts/public-subscription";

function getBackendApiBaseUrl() {
  const configuredBaseUrl =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/";

  return configuredBaseUrl.endsWith("/")
    ? configuredBaseUrl
    : `${configuredBaseUrl}/`;
}

export async function GET(
  request: Request,
  context: { params: Promise<{ token: string }> },
) {
  const { token } = await context.params;
  const requestUrl = new URL(request.url);
  const headers = new Headers();
  const forwardedFor = request.headers.get("x-forwarded-for");
  if (forwardedFor) {
    headers.set("X-Forwarded-For", forwardedFor);
  }
  const realIp = request.headers.get("x-real-ip");
  if (realIp) {
    headers.set("X-Real-IP", realIp);
  }
  const deviceKey =
    request.headers.get("x-device-key") ?? requestUrl.searchParams.get("device_key");
  if (deviceKey) {
    headers.set("X-Device-Key", deviceKey);
  }
  const userAgent = request.headers.get("user-agent");
  if (userAgent) {
    headers.set("User-Agent", userAgent);
  }
  const response = await fetch(
    new URL(publicSubscriptionApiPaths.feed(token), getBackendApiBaseUrl()),
    {
      headers,
      cache: "no-store",
    },
  );

  return new Response(await response.text(), {
    status: response.status,
    headers: {
      "Content-Type":
        response.headers.get("Content-Type") ?? "text/plain; charset=utf-8",
    },
  });
}
