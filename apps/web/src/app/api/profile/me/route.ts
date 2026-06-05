import { proxyBackendAuthRequest } from "@/shared/auth/backend-auth-proxy";

export async function GET(request: Request) {
  return proxyBackendAuthRequest({
    pathname: "profile/me/",
    method: "GET",
    authorization: request.headers.get("Authorization"),
  });
}

export async function PATCH(request: Request) {
  const body = await request.json();

  return proxyBackendAuthRequest({
    pathname: "profile/me/",
    method: "PATCH",
    authorization: request.headers.get("Authorization"),
    body,
  });
}
