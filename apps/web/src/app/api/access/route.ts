import { accessApiPaths } from "@infinda/shared/contracts/access";
import { proxyBackendAuthRequest } from "@/shared/auth/backend-auth-proxy";

export async function GET(request: Request) {
  return proxyBackendAuthRequest({
    pathname: accessApiPaths.current,
    method: "GET",
    authorization: request.headers.get("Authorization"),
  });
}
