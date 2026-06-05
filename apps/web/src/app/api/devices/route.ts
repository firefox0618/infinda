import { devicesApiPaths } from "@infinda/shared/contracts/devices";
import { proxyBackendAuthRequest } from "@/shared/auth/backend-auth-proxy";

export async function GET(request: Request) {
  return proxyBackendAuthRequest({
    pathname: devicesApiPaths.list,
    method: "GET",
    authorization: request.headers.get("Authorization"),
  });
}
