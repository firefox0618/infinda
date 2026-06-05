import { proxyBackendAuthRequest } from "@/shared/auth/backend-auth-proxy";

export async function POST(request: Request) {
  return proxyBackendAuthRequest({
    pathname: "auth/logout/",
    method: "POST",
    authorization: request.headers.get("Authorization"),
  });
}
