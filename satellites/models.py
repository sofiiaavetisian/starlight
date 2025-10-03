from django.db import models
from django.conf import settings

class TLE(models.Model):
    norad_id = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=128, blank=True)
    line1 = models.CharField(max_length=80)
    line2 = models.CharField(max_length=80)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.norad_id} {self.name}".strip()

class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
        null=True,
        blank=True,
    )
    norad_id = models.PositiveIntegerField()
    name = models.CharField(max_length=128)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("user", "norad_id")

    def __str__(self):
        return f"{self.name} ({self.norad_id})"
