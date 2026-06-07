import { telegramApiPaths } from "@infinda/shared/contracts/telegram";

import { proxyBackendAuthRequest } from "@/shared/auth/backend-auth-proxy";

export async function GET(request: Request) {
  return proxyBackendAuthRequest({
    pathname: telegramApiPaths.link,
    method: "GET",
    authorization: request.headers.get("Authorization"),
  });
}

export async function POST(request: Request) {
  return proxyBackendAuthRequest({
    pathname: telegramApiPaths.link,
    method: "POST",
    authorization: request.headers.get("Authorization"),
  });
}

export async function DELETE(request: Request) {
  return proxyBackendAuthRequest({
    pathname: telegramApiPaths.link,
    method: "DELETE",
    authorization: request.headers.get("Authorization"),
  });
}
