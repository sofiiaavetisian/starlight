from __future__ import annotations
from datetime import datetime, timezone
from sgp4.api import Satrec, jday
from pyproj import Transformer
import math

_ecef_to_geodetic = Transformer.from_crs("epsg:4978", "epsg:4979", always_xy=True)

def _teme_to_ecef(r_teme_km, v_teme_kms, dt: datetime):
    """
    Convert TEME (SGP4 output) to ECEF using a simple GMST rotation.
    - Uses UTC as an approximation for UT1 (adequate for most apps without EOPs).
    - Ignores polar motion; accuracy is typically within a few hundred meters.
    Returns ECEF position vector in kilometers.
    """
    # Julian date for the provided UTC time
    jd, fr = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second + dt.microsecond/1e6)
    theta = _gmst_from_jd(jd + fr)  # Greenwich Mean Sidereal Time (radians)

    cos_t = math.cos(theta)
    sin_t = math.sin(theta)

    x_t, y_t, z_t = r_teme_km
    # Rotate about Z to obtain Earth-fixed coordinates
    x_e = cos_t * x_t + sin_t * y_t
    y_e = -sin_t * x_t + cos_t * y_t
    z_e = z_t
    return (x_e, y_e, z_e)

def _gmst_from_jd(jd_ut1: float) -> float:
    """
    Compute Greenwich Mean Sidereal Time (GMST) in radians from Julian date (UT1≈UTC).
    Uses a standard approximation sufficient for visualization and general tracking.
    Reference: IAU conventions (approx) / Meeus. Accuracy ~<0.1s of time for many dates.
    """
    T = (jd_ut1 - 2451545.0) / 36525.0
    gmst_deg = (
        280.46061837
        + 360.98564736629 * (jd_ut1 - 2451545.0)
        + 0.000387933 * T * T
        - (T ** 3) / 38710000.0
    )
    gmst_deg = gmst_deg % 360.0
    return math.radians(gmst_deg)

# for this function, i simplified teh sgp4 algorithm available online to meet my basic needs
# we need this function to propagate the satellite position to the current time based on its time and orbit epoch
def propagate_now(line1: str, line2: str, *, at: datetime | None = None):
    now = at.astimezone(timezone.utc) if at else datetime.now(timezone.utc)
    sat = Satrec.twoline2rv(line1, line2)
    jd, fr = jday(now.year, now.month, now.day, now.hour, now.minute, now.second + now.microsecond/1e6)
    e, r, v = sat.sgp4(jd, fr) 
    if e != 0:
        raise ValueError(f"SGP4 error code {e}")

    x, y, z = _teme_to_ecef(r, v, now)
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
