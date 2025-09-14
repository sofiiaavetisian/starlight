from rest_framework import serializers
from .models import Favorite
from .models import TLE

class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ["id", "norad_id", "name", "notes", "created_at"]

class TLESerializer(serializers.ModelSerializer):
    class Meta:
        model = TLE
        fields = ["norad_id", "name", "line1", "line2", "updated_at"]
