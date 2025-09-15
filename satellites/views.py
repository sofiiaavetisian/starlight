from django.shortcuts import render
from rest_framework import generics, filters
from .models import TLE
from .serializers import TLESerializer
from .services.tle_fetcher import get_or_refresh_tle, TLENotFound
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from .models import Favorite
from .serializers import FavoriteSerializer

class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer

@api_view(["GET"])
def position_single(request, norad_id: int):
    try:
        name, l1, l2 = get_or_refresh_tle(norad_id, max_age_hours=48)
    except TLENotFound as e:
        return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
    pos = propagate_now(l1, l2)
    return Response({"norad_id": norad_id, "name": name, **pos})

@api_view(["GET"])
def positions_batch(request):
    out = []
    for fav in Favorite.objects.all():
        try:
            name, l1, l2 = get_or_refresh_tle(fav.norad_id, max_age_hours=48)
            pos = propagate_now(l1, l2)
            out.append({"norad_id": fav.norad_id, "name": name, **pos})
        except TLENotFound:
            continue
    return Response(out)

class SatelliteListView(generics.ListAPIView):
    """
    Read-only catalog list. Supports ?search=iss or ?search=25544
    and simple ordering by name or norad_id: ?ordering=name or ?ordering=-norad_id
    """
    queryset = TLE.objects.all().order_by("norad_id")
    serializer_class = TLESerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "norad_id"]
    ordering_fields = ["name", "norad_id"]
    pagination_class = None  # set DRF pagination if you want pages

@api_view(["POST"])
def import_tle_catalog(request):
    return Response({"detail": "Not implemented yet."})