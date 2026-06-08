import { accessApiPaths } from "@infinda/shared/contracts/access";
import { proxyBackendAuthRequest } from "@/shared/auth/backend-auth-proxy";

export async function POST(request: Request) {
  return proxyBackendAuthRequest({
    pathname: accessApiPaths.sync,
    method: "POST",
    authorization: request.headers.get("Authorization"),
  });
}
