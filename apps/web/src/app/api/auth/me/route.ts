import { proxyBackendAuthRequest } from "@/shared/auth/backend-auth-proxy";

export async function GET(request: Request) {
  return proxyBackendAuthRequest({
    pathname: "auth/me/",
    method: "GET",
    authorization: request.headers.get("Authorization"),
  });
}
