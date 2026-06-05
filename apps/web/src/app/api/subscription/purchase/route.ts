import { subscriptionApiPaths } from "@infinda/shared/contracts/subscription";
import { proxyBackendAuthRequest } from "@/shared/auth/backend-auth-proxy";

export async function POST(request: Request) {
  const body = await request.json();

  return proxyBackendAuthRequest({
    pathname: subscriptionApiPaths.purchase,
    method: "POST",
    authorization: request.headers.get("Authorization"),
    body,
  });
}
