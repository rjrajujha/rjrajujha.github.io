from django.contrib import admin

from .models import ChatbotLog


@admin.register(ChatbotLog)
class ChatbotLogAdmin(admin.ModelAdmin):
    list_display = ("provider", "created_at")
    search_fields = ("user_message", "assistant_response")
    readonly_fields = ("provider", "user_message", "assistant_response", "created_at")
    ordering = ("-created_at",)
