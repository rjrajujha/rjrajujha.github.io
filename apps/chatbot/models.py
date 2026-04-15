from django.db import models


class ChatbotLog(models.Model):
    provider = models.CharField(max_length=30)
    user_message = models.TextField()
    assistant_response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.provider} @ {self.created_at:%Y-%m-%d %H:%M}"
