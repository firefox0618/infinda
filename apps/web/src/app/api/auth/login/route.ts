import { proxyBackendAuthRequest } from "@/shared/auth/backend-auth-proxy";

export async function POST(request: Request) {
  const body = await request.json();

  return proxyBackendAuthRequest({
    pathname: "auth/login/",
    method: "POST",
    body,
  });
}
