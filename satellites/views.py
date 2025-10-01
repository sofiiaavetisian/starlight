from datetime import datetime
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from rest_framework import generics, filters
from .models import TLE
from .serializers import TLESerializer
from .services.tle_fetcher import get_or_refresh_tle, TLENotFound
from .services.propagation import propagate_now
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from .models import Favorite
from .serializers import FavoriteSerializer


def _catalog_label(tle: TLE) -> str:
    name = (tle.name or "").strip()
    return name or f"NORAD {tle.norad_id}"

class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer

def home(request):
    return render(request, "home.html")


def catalog(request):
    satellites = [
        {
            "norad_id": tle.norad_id,
            "name": (tle.name or "").strip(),
            "label": _catalog_label(tle),
        }
        for tle in TLE.objects.all()
    ]
    satellites.sort(key=lambda entry: entry["label"].lower())
    context = {
        "satellites": satellites,
        "search_term": request.GET.get("q", "").strip(),
    }
    return render(request, "catalog.html", context)


def catalog_search(request):
    query = (request.GET.get("search") or "").strip()
    if not query:
        messages.info(request, "Enter a satellite name or NORAD ID to search.")
        return redirect("catalog")

    satellite = None
    if query.isdigit():
        satellite = TLE.objects.filter(norad_id=int(query)).first()

    if satellite is None:
        satellite = TLE.objects.filter(name__iexact=query).first()

    if satellite is None:
        satellite = TLE.objects.filter(name__icontains=query).order_by("name").first()

    if satellite:
        return redirect("satellite-detail", norad_id=satellite.norad_id)

    messages.error(request, f"No satellite found for \"{query}\".")
    catalog_url = f"{reverse('catalog')}?q={query}"
    return redirect(catalog_url)


def satellite_detail(request, norad_id: int):
    tle = get_object_or_404(TLE, pk=norad_id)
    try:
        name, line1, line2 = get_or_refresh_tle(norad_id, max_age_hours=48)
    except TLENotFound:
        name = (tle.name or "").strip()
        line1, line2 = tle.line1, tle.line2

    try:
        stats = propagate_now(line1, line2)
    except ValueError as error:
        stats = None
        error_message = str(error)
    else:
        error_message = None

    clean_name = (name or "").strip()
    label = clean_name or f"NORAD {norad_id}"

    if stats and stats.get("timestamp"):
        try:
            stats["timestamp_obj"] = datetime.fromisoformat(stats["timestamp"])
        except ValueError:
            stats["timestamp_obj"] = None


    context = {
        "satellite": {
            "norad_id": norad_id,
            "name": clean_name,
            "label": label,
        },
        "stats": stats,
        "error": error_message,
    }
    return render(request, "satellite_detail.html", context)


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
