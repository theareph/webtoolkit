from django.contrib import admin

from . import models


@admin.register(models.ShortenedURL)
class ShortenedURLAdmin(admin.ModelAdmin):  # pyright: ignore[reportMissingTypeArgument]
    raw_id_fields = ["owner"]
    list_display = ["alias", "url_display", "owner"]
    readonly_fields = ["inserted_at", "updated_at"]

    def url_display(self, obj):
        return (obj.url or "")[:100]
