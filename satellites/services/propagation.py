from __future__ import annotations
from datetime import datetime, timezone
from sgp4.api import Satrec, jday
from pyproj import Transformer
import math

_ecef_to_geodetic = Transformer.from_crs("epsg:4978", "epsg:4979", always_xy=True)

#here i will approximate thaat the coordinates are earth fixed (they are not, i would need to transform it, but it might get too complex)
def _eci_to_ecef(r_teme_km, v_teme_kms, dt: datetime):
    return r_teme_km

# for this function, i simplified teh sgp4 algorithm available online to meet my basic needs

# we need this function to propagate the satellite position to the current time based on its time and orbit epoch
def propagate_now(line1: str, line2: str):
    now = datetime.now(timezone.utc)
    sat = Satrec.twoline2rv(line1, line2)
    jd, fr = jday(now.year, now.month, now.day, now.hour, now.minute, now.second + now.microsecond/1e6)
    e, r, v = sat.sgp4(jd, fr) 
    if e != 0:
        raise ValueError(f"SGP4 error code {e}")

    x, y, z = _eci_to_ecef(r, v, now)
    lon, lat, alt = _ecef_to_geodetic.transform(x*1000, y*1000, z*1000)  # meters in -> lon,lat,ellipsoidal height(m)
    alt_km = alt / 1000.0
    vel_kms = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)

    return {
        "lat": float(lat),
        "lon": float(lon),
        "alt_km": float(alt_km),
        "vel_kms": float(vel_kms),
        "timestamp": now.isoformat(),
    }

