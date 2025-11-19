from rest_framework import serializers

from .models import Favorite
from .models import TLE
from .services.favorites import serialize_favorite

# serializers are used to convert django model data to and from JSON

class FavoriteSerializer(serializers.ModelSerializer):
    """Serializer for the Favorite model."""
    class Meta:
        model = Favorite
        fields = ["id", "norad_id", "name", "notes", "created_at"]

    def to_representation(self, instance):
        """Delegate favorite serialization to the dedicated service for consistency."""
        return serialize_favorite(instance)

class TLESerializer(serializers.ModelSerializer):
    """Serializer for the TLE model."""
    class Meta:
        model = TLE
        fields = ["norad_id", "name", "line1", "line2", "updated_at"]
