import { proxyBackendAuthRequest } from "@/shared/auth/backend-auth-proxy";

export async function GET(request: Request) {
  return proxyBackendAuthRequest({
    pathname: "devices/",
    method: "GET",
    authorization: request.headers.get("Authorization"),
  });
}
