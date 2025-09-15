from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FavoriteViewSet, position_single, positions_batch, import_tle_catalog,
    SatelliteListView,
)

router = DefaultRouter()
router.register(r"favorites", FavoriteViewSet, basename="favorite")

urlpatterns = [
    path("", include(router.urls)),
    path("satellites/", SatelliteListView.as_view(), name="satellites-list"),
    path("position/<int:norad_id>/", position_single, name="position-single"),
    path("positions/", positions_batch, name="positions-batch"),
    path("tle/import/", import_tle_catalog, name="tle-import"),
]
