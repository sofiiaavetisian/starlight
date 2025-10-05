from datetime import datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
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
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import CreateView
from django.urls import reverse_lazy

""" In this file are the views for the satellites app, including web pages and API endpoints. """

def _catalog_label(tle: TLE) -> str:
    """Generate a display label for a satellite in the catalog"""
    name = (tle.name or "").strip()
    return name or f"NORAD {tle.norad_id}"

class FavoriteViewSet(viewsets.ModelViewSet):
    """API endpoint for viewing and editing user favorites"""
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer

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

    satellites = [
        {
            "norad_id": tle.norad_id,
            "name": (tle.name or "").strip(),
            "label": _catalog_label(tle),
        }
        for tle in TLE.objects.all() # get all TLE entries
    ]
    satellites.sort(key=lambda entry: entry["label"].lower()) # sort by label, case-insensitive
    
    # render the catalog template with the satellites and search term
    context = {
        "satellites": satellites,
        "search_term": request.GET.get("q", "").strip(),
    }
    return render(request, "catalog.html", context)


def catalog_search(request):
    """Handle search requests from the catalog page."""

    # get the search query from the request
    query = (request.GET.get("search") or "").strip()
    if not query:
        messages.info(request, "Enter a satellite name or NORAD ID to search.")
        return redirect("catalog")

    satellite = None

    # first try to match by NORAD ID if the query is all digits
    if query.isdigit():
        satellite = TLE.objects.filter(norad_id=int(query)).first()
    
    # try exact name match (case-insensitive)
    if satellite is None:
        satellite = TLE.objects.filter(name__iexact=query).first()

    # try partial name match (case-insensitive)
    if satellite is None:
        satellite = TLE.objects.filter(name__icontains=query).order_by("name").first()

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

    try:
        # here we try to get a recent TLE fetching from CelesTrak if needed using our get_or_refresh_tle function
        name, line1, line2 = get_or_refresh_tle(norad_id, max_age_hours=48)

    except TLENotFound:
        name = (tle.name or "").strip()
        line1, line2 = tle.line1, tle.line2

    try:
        # propagate to current position using our propagate_now function
        stats = propagate_now(line1, line2)

    except ValueError as error:
        stats = None
        error_message = str(error)
    else:
        error_message = None

    clean_name = (name or "").strip()
    label = clean_name or f"NORAD {norad_id}"

    # parse the timestamp into a datetime object for template use
    if stats and stats.get("timestamp"):
        try:
            stats["timestamp_obj"] = datetime.fromisoformat(stats["timestamp"])
        except ValueError:
            stats["timestamp_obj"] = None

    # render the detail template with the satellite info, stats, and any error message
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(user=request.user, norad_id=norad_id).exists()

    context = {
        "satellite": {
            "norad_id": norad_id,
            "name": clean_name,
            "label": label,
        },
        "stats": stats,
        "error": error_message,
        "is_favorite": is_favorite,
    }
    return render(request, "satellite_detail.html", context)


@api_view(["GET"])
def position_single(request, norad_id: int):
    """Given a NORAD ID, return the current position of the satellite as JSON."""
    try:
        # get or update the TLE for the satellite by NORAD ID
        name, l1, l2 = get_or_refresh_tle(norad_id, max_age_hours=48)

    except TLENotFound as e:
        return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
    # propagate to current position
    pos = propagate_now(l1, l2)

    # return the position info as JSON
    return Response({"norad_id": norad_id, "name": name, **pos})

@api_view(["GET"])
def positions_batch(request):
    out = []
    for fav in Favorite.objects.all():
        try:
            # get or update the TLE for the favorite satellites
            name, l1, l2 = get_or_refresh_tle(fav.norad_id, max_age_hours=48)
            # propagate to current position
            pos = propagate_now(l1, l2)
            # add to output list
            out.append({"norad_id": fav.norad_id, "name": name, **pos})
        except TLENotFound:
            continue
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
