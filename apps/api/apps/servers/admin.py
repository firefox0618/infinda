from django.contrib import admin

from .models import Server, ServerLocation, ServerStatusSnapshot


@admin.register(ServerLocation)
class ServerLocationAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name", "region", "country_code")
    search_fields = ("code", "name", "region", "country_code")


class ServerStatusSnapshotInline(admin.TabularInline):
    model = ServerStatusSnapshot
    extra = 0
    fields = ("status", "latency_ms", "active_connections", "error_reason", "checked_at")
    readonly_fields = ("checked_at",)
    ordering = ("-checked_at", "-id")


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "code",
        "name",
        "location",
        "provider",
        "status",
        "used_capacity_units",
        "capacity_units",
        "last_heartbeat",
    )
    list_filter = ("status", "provider", "location")
    search_fields = ("code", "name", "hostname", "ip_address")
    autocomplete_fields = ("location",)
    inlines = [ServerStatusSnapshotInline]


@admin.register(ServerStatusSnapshot)
class ServerStatusSnapshotAdmin(admin.ModelAdmin):
    list_display = ("id", "server", "status", "latency_ms", "active_connections", "checked_at")
    list_filter = ("status", "checked_at")
    search_fields = ("server__code", "server__name", "error_reason")
    autocomplete_fields = ("server",)
