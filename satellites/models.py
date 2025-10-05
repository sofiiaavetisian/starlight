from django.db import models
from django.conf import settings

#Each model class represents a table in the database.

class TLE(models.Model):
    """
    Represents a satellite's Two-Line Element (TLE) data.
    """
    norad_id = models.PositiveIntegerField(primary_key=True) # unique NORAD ID
    name = models.CharField(max_length=128, blank=True) # satellite name
    line1 = models.CharField(max_length=80) # 1st of TLE data
    line2 = models.CharField(max_length=80) # 2nd of TLE data
    updated_at = models.DateTimeField(auto_now=True) # timestamp of last update

    def __str__(self):
        # shows norad_id and name
        return f"{self.norad_id} {self.name}".strip()

class Favorite(models.Model):
    """User's favorite satellites."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites") # link to user
    norad_id = models.PositiveIntegerField() # NORAD ID of the satellite
    name = models.CharField(max_length=128) # satellite name
    notes = models.TextField(blank=True) # user notes
    created_at = models.DateTimeField(auto_now_add=True) # timestamp of creation

    class Meta:

        """Meta options for the Favorite model."""
        ordering = ["-created_at"] # newest first
        unique_together = ("user", "norad_id") # unique per user

    def __str__(self):
        # shows name and norad_id
        return f"{self.name} ({self.norad_id})"
