from rest_framework import serializers
from .models import Favorite
from .models import TLE

# serializers are used to convert django model data to and from JSON

class FavoriteSerializer(serializers.ModelSerializer):
    """Serializer for the Favorite model."""
    class Meta:
        model = Favorite
        fields = ["id", "norad_id", "name", "notes", "created_at"]

class TLESerializer(serializers.ModelSerializer):
    """Serializer for the TLE model."""
    class Meta:
        model = TLE
        fields = ["norad_id", "name", "line1", "line2", "updated_at"]
