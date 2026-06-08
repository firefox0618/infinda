from rest_framework.response import Response
from rest_framework.views import APIView

from apps.servers.services import build_server_runtime_summary


class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        runtime_summary = build_server_runtime_summary()
        health_status = (
            "degraded"
            if runtime_summary["offline_server_count"] > 0
            or runtime_summary["degraded_server_count"] > 0
            or runtime_summary["maintenance_server_count"] > 0
            else "ok"
        )
        return Response(
            {
                "status": health_status,
                "service": "api",
                "runtime": runtime_summary,
            }
        )
