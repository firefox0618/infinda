import { devicesApiPaths } from "@infinda/shared/contracts/devices";
import { proxyBackendAuthRequest } from "@/shared/auth/backend-auth-proxy";

type RouteContext = {
  params: Promise<{
    deviceId: string;
  }>;
};

export async function POST(request: Request, context: RouteContext) {
  const { deviceId } = await context.params;
  const rawBody = await request.text();

  return proxyBackendAuthRequest({
    pathname: devicesApiPaths.revoke(deviceId),
    method: "POST",
    authorization: request.headers.get("Authorization"),
    body: rawBody ? JSON.parse(rawBody) : undefined,
  });
}
