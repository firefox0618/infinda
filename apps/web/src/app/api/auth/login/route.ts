import { authApiPaths } from "@infinda/shared/contracts/auth";
import { proxyBackendAuthRequest } from "@/shared/auth/backend-auth-proxy";

export async function POST(request: Request) {
  const body = await request.json();

  return proxyBackendAuthRequest({
    pathname: authApiPaths.login,
    method: "POST",
    body,
  });
}
