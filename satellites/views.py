from django.shortcuts import render

from .services.tle_fetcher import get_or_refresh_tle, TLENotFound

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

