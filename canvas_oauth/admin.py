from django.contrib import admin
from canvas_oauth.models import CanvasOAuth2Token


class CanvasOAuth2TokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'expires', 'created_on', 'updated_on')
    search_fields = ('user',)


admin.site.register(CanvasOAuth2Token, CanvasOAuth2TokenAdmin)
