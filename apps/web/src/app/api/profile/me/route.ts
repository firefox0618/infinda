import { profileApiPaths } from "@infinda/shared/contracts/profile";
import { proxyBackendAuthRequest } from "@/shared/auth/backend-auth-proxy";

export async function GET(request: Request) {
  return proxyBackendAuthRequest({
    pathname: profileApiPaths.me,
    method: "GET",
    authorization: request.headers.get("Authorization"),
  });
}

export async function PATCH(request: Request) {
  const body = await request.json();

  return proxyBackendAuthRequest({
    pathname: profileApiPaths.me,
    method: "PATCH",
    authorization: request.headers.get("Authorization"),
    body,
  });
}
