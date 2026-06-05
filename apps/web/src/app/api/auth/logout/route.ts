import { authApiPaths } from "@infinda/shared/contracts/auth";
import { proxyBackendAuthRequest } from "@/shared/auth/backend-auth-proxy";

export async function POST(request: Request) {
  return proxyBackendAuthRequest({
    pathname: authApiPaths.logout,
    method: "POST",
    authorization: request.headers.get("Authorization"),
  });
}
