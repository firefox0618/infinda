from django.core.management.base import BaseCommand

from apps.provisioning.services import refresh_enabled_provisioning_servers


class Command(BaseCommand):
    help = "Actively checks enabled provisioning servers and updates runtime snapshots."

    def handle(self, *args, **options):
        checks = refresh_enabled_provisioning_servers()
        if not checks:
            self.stdout.write(self.style.WARNING("No enabled provisioning servers found."))
            return

        for item in checks:
            line = (
                f"{item['server_code']}: status={item['status']} "
                f"adapter={item['adapter']} latency_ms={item['latency_ms']} "
                f"error_code={item['error_code'] or '-'}"
            )
            if item["status"] == "active":
                self.stdout.write(self.style.SUCCESS(line))
            else:
                self.stdout.write(self.style.WARNING(line))
