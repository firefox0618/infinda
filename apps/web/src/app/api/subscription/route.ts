import { subscriptionApiPaths } from "@infinda/shared/contracts/subscription";
import { proxyBackendAuthRequest } from "@/shared/auth/backend-auth-proxy";

export async function GET(request: Request) {
  return proxyBackendAuthRequest({
    pathname: subscriptionApiPaths.current,
    method: "GET",
    authorization: request.headers.get("Authorization"),
  });
}
