import { supportApiPaths } from "@infinda/shared/contracts/support";

import { proxyBackendMultipartRequest } from "@/shared/auth/backend-auth-proxy";

export async function POST(request: Request) {
  const body = await request.formData();

  return proxyBackendMultipartRequest({
    pathname: supportApiPaths.messages,
    method: "POST",
    authorization: request.headers.get("Authorization"),
    body,
  });
}
