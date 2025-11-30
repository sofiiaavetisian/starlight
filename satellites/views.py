from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from rest_framework import generics, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .models import Favorite, TLE
from .serializers import FavoriteSerializer, TLESerializer
from .services.catalog import list_catalog_entries, search_catalog
from .services.tracking import (
    favorite_positions_for_user,
    satellite_detail_payload,
    satellite_position_payload,
)
from satellites.services.tle_fetcher import TLENotFound
import logging
logger = logging.getLogger(__name__)


""" In this file are the views for the satellites app, including web pages and API endpoints. """

class FavoriteViewSet(viewsets.ModelViewSet):
    """API endpoint for viewing and editing user favorites for the authenticated user."""

    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Favorite.objects.none()
        return Favorite.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        """Tie newly created favorites to the requesting user."""
        serializer.save(user=self.request.user)

class SignUpView(CreateView):
    """View for user signup."""
    form_class = UserCreationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("login")

def home(request):
    """Home page view"""
    return render(request, "home.html")


@login_required
def favorites_list(request):
    """List all satellites the current user has marked as a favorite."""
    favorites = request.user.favorites.all()
    return render(request, "favorites/list.html", {"favorites": favorites})


@login_required
@require_POST
def favorite_add(request, norad_id: int):
    """Add a satellite to the current user's favorites, ignoring duplicates."""
    tle = get_object_or_404(TLE, pk=norad_id)
    label = (tle.name or "").strip() or f"NORAD {tle.norad_id}"
    Favorite.objects.get_or_create(
        user=request.user,
        norad_id=norad_id,
        defaults={"name": label},
    )
    next_url = request.POST.get("next") or reverse("satellite-detail", args=[norad_id])
    return redirect(next_url)


@login_required
@require_POST
def favorite_remove(request, norad_id: int):
    """Remove a satellite from the current user's favorites if it exists."""
    Favorite.objects.filter(user=request.user, norad_id=norad_id).delete()
    next_url = request.POST.get("next") or reverse("favorites")
    return redirect(next_url)


def catalog(request):
    """View for the satellite catalog page."""
    logger.info("Catalog view: start")

    satellites = list_catalog_entries()
    logger.info("Catalog view: loaded %s satellites", len(satellites))

    context = {
        "satellites": satellites,
        "search_term": request.GET.get("q", "").strip(),
    }
    logger.info("Catalog view: rendering template")
    return render(request, "catalog.html", context)


def catalog_search(request):
    """Handle search requests from the catalog page."""

    # get the search query from the request
    query = (request.GET.get("search") or "").strip()
    if not query:
        messages.info(request, "Enter a satellite name or NORAD ID to search.")
        return redirect("catalog")

    satellite = search_catalog(query)

    #if we found a satellite redirect to its detail page
    if satellite:
        return redirect("satellite-detail", norad_id=satellite.norad_id)

    messages.error(request, f"No satellite found for \"{query}\".")
    catalog_url = f"{reverse('catalog')}?q={query}" 

    # redirect back to catalog with the search term
    return redirect(catalog_url)


def satellite_detail(request, norad_id: int):

    """View for a single satellite's detail page that shows current position."""

    tle = get_object_or_404(TLE, pk=norad_id) # get the TLE or 404 (Django shortcut)
    payload = satellite_detail_payload(tle)
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(user=request.user, norad_id=norad_id).exists()

    payload["is_favorite"] = is_favorite
    return render(request, "satellite_detail.html", payload)


@api_view(["GET"])
def position_single(request, norad_id: int):
    """Given a NORAD ID, return the current position of the satellite as JSON."""
    try:
        payload = satellite_position_payload(norad_id)
    except TLE.DoesNotExist:
        return Response({"detail": "Satellite not found."}, status=status.HTTP_404_NOT_FOUND)
    except TLENotFound as e:
        return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    # return the position info as JSON
    return Response(payload)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def positions_batch(request):
    out = favorite_positions_for_user(request.user)
    return Response(out)

class SatelliteListView(generics.ListAPIView): 
    """API view to list satellites"""

    # so when someone requests /api/satellites/, this view handles the request and returns a list of satellites as JSON 
    queryset = TLE.objects.all().order_by("norad_id")
    serializer_class = TLESerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "norad_id"]
    ordering_fields = ["name", "norad_id"]
    pagination_class = None 
