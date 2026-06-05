import { authApiPaths } from "@infinda/shared/contracts/auth";
import { proxyBackendAuthRequest } from "@/shared/auth/backend-auth-proxy";

export async function GET(request: Request) {
  return proxyBackendAuthRequest({
    pathname: authApiPaths.me,
    method: "GET",
    authorization: request.headers.get("Authorization"),
  });
}
