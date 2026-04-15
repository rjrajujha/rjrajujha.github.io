from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "is_featured", "display_order", "updated_at")
    list_filter = ("is_featured",)
    search_fields = ("title", "headline", "description", "tech_stack")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("display_order", "title")
