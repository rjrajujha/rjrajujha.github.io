from django.db import models


class Project(models.Model):
    title = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    headline = models.CharField(max_length=180)
    description = models.TextField()
    tech_stack = models.CharField(max_length=255, help_text="Comma-separated technologies")
    impact = models.CharField(max_length=180, blank=True)
    source_url = models.URLField(blank=True)
    demo_url = models.URLField(blank=True)
    is_featured = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "title"]

    def __str__(self) -> str:
        return self.title

    @property
    def stack_items(self) -> list[str]:
        return [item.strip() for item in self.tech_stack.split(",") if item.strip()]
