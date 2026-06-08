import { headers } from "next/headers";
import { notFound } from "next/navigation";

import type { PublicSubscriptionSummaryDto } from "@infinda/shared/contracts/public-subscription";
import { publicSubscriptionApiPaths } from "@infinda/shared/contracts/public-subscription";
import { PublicSubscriptionPage } from "@/features/public-subscription-page/components/public-subscription-page";

function getBackendApiBaseUrl() {
  const configuredBaseUrl =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/";

  return configuredBaseUrl.endsWith("/")
    ? configuredBaseUrl
    : `${configuredBaseUrl}/`;
}

async function loadPublicSubscription(token: string) {
  const requestHeaders = await headers();
  const forwardedHeaders = new Headers();
  const forwardedFor = requestHeaders.get("x-forwarded-for");
  if (forwardedFor) {
    forwardedHeaders.set("X-Forwarded-For", forwardedFor);
  }
  const realIp = requestHeaders.get("x-real-ip");
  if (realIp) {
    forwardedHeaders.set("X-Real-IP", realIp);
  }
  const response = await fetch(
    new URL(publicSubscriptionApiPaths.summary(token), getBackendApiBaseUrl()),
    {
      headers: forwardedHeaders,
      cache: "no-store",
    },
  );

  if (response.status === 404) {
    notFound();
  }

  if (!response.ok) {
    throw new Error("Failed to load public subscription.");
  }

  return (await response.json()) as PublicSubscriptionSummaryDto;
}

type PageProps = {
  params: Promise<{
    token: string;
  }>;
};

export default async function Page({ params }: PageProps) {
  const { token } = await params;
  const subscription = await loadPublicSubscription(token);

  return <PublicSubscriptionPage token={token} subscription={subscription} />;
}
