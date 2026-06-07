from django.contrib import admin

from .models import ConnectionRoute, ProductLocation


@admin.register(ProductLocation)
class ProductLocationAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name", "sort_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name")


@admin.register(ConnectionRoute)
class ConnectionRouteAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name", "location", "server", "protocol", "is_active", "priority")
    list_filter = ("is_active", "protocol", "location", "server__status")
    search_fields = ("code", "name", "endpoint_url", "server__code")
    autocomplete_fields = ("location", "server")
