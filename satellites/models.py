from django.db import models

class TLE(models.Model):
    norad_id = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=128, blank=True)
    line1 = models.CharField(max_length=80)
    line2 = models.CharField(max_length=80)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.norad_id} {self.name}".strip()

class Favorite(models.Model):
    norad_id = models.PositiveIntegerField()
    name = models.CharField(max_length=128)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.norad_id})"

