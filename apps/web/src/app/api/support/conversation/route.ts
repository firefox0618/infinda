import { supportApiPaths } from "@infinda/shared/contracts/support";

import { proxyBackendAuthRequest } from "@/shared/auth/backend-auth-proxy";

export async function GET(request: Request) {
  return proxyBackendAuthRequest({
    pathname: supportApiPaths.conversation,
    method: "GET",
    authorization: request.headers.get("Authorization"),
  });
}

