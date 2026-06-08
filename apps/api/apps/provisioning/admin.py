from django.contrib import admin

from .models import ProvisionedDeviceAccess, ProvisioningOperation, ServerProvisioningProfile


@admin.register(ServerProvisioningProfile)
class ServerProvisioningProfileAdmin(admin.ModelAdmin):
    list_display = (
        "server",
        "adapter",
        "is_enabled",
        "panel_base_url",
        "default_inbound_id",
        "external_node_key",
        "updated_at",
    )
    list_filter = ("adapter", "is_enabled")
    search_fields = ("server__code", "server__name", "external_node_key", "panel_base_url")


@admin.register(ProvisioningOperation)
class ProvisioningOperationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "operation_type",
        "trigger",
        "status",
        "server",
        "route",
        "created_at",
        "finished_at",
    )
    list_filter = ("operation_type", "trigger", "status", "adapter")
    search_fields = ("user__username", "server__code", "route__code", "error_code")
    readonly_fields = ("created_at", "updated_at", "finished_at")


@admin.register(ProvisionedDeviceAccess)
class ProvisionedDeviceAccessAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "device",
        "route",
        "server",
        "status",
        "adapter",
        "external_client_email",
        "inbound_id",
        "last_synced_at",
    )
    list_filter = ("status", "adapter", "server")
    search_fields = (
        "user__username",
        "device__name",
        "route__code",
        "server__code",
        "external_client_uuid",
        "external_client_email",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "provisioned_at",
        "last_synced_at",
        "revoked_at",
    )
