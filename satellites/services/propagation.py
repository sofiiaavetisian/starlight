from __future__ import annotations
from datetime import datetime, timezone
from sgp4.api import Satrec, jday
from pyproj import Transformer
import math

_ecef_to_geodetic = Transformer.from_crs("epsg:4978", "epsg:4979", always_xy=True)

def _teme_to_ecef(r_teme_km, v_teme_kms, dt: datetime):
    """
    This function converts the TEME vector (SGP4 output) to ECEF (whoch means: Earth-Centered, Earth-Fixed). 
    So what it does is rotating the orbit vector (TEME) so it matches Earth's frame instead of the satellite's frame.
    For the sake of simplicity, I will ignore polar motion, beacuse accuracy is typically within a few hundred meters.
   
    --> returns ECEF position vector in kilometers that we will use in propagate_now function.
    """
    # julian date for the provided UTC time
    jd, fr = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second + dt.microsecond/1e6)

    theta = _gmst_from_jd(jd + fr)  # Greenwich Mean Sidereal Time (radians)

    cos_t = math.cos(theta)
    sin_t = math.sin(theta)

    x_t, y_t, z_t = r_teme_km

    # No velocity transformation is done here; only position is converted.
    # Rotate about Z to obtain Earth-fixed coordinates
    x_e = cos_t * x_t + sin_t * y_t
    y_e = -sin_t * x_t + cos_t * y_t
    z_e = z_t

    return (x_e, y_e, z_e)

def _gmst_from_jd(jd_ut1: float) -> float:
    """
    This function computes the earths rotation angle (Greenwich Mean Sidereal Time) at the exact timestamp im propagating to.
    It computes the GMST based on the Julian date passed to it (time at whcih we want to see the satellite's position).

    --> returns the GMST in radians (used to rotate the TEME coordinates to ECEF coordinates to exact point of time)
    """
    # calculating the number of centuries since J2000.0
    T = (jd_ut1 - 2451545.0) / 36525.0

    # compute GMST in degrees
    gmst_deg = ( 280.46061837 + 360.98564736629 * (jd_ut1 - 2451545.0) + 0.000387933 * T * T - (T ** 3) / 38710000.0 )
    gmst_deg = gmst_deg % 360.0

    return math.radians(gmst_deg)

# for this function, i simplified teh sgp4 algorithm available online to meet my basic needs
# we need this function to propagate the satellite position to the current time based on its time and orbit epoch

def propagate_now(line1: str, line2: str):
    """Taking the raw fetched TLE lines and propagate them to "right now" so I can plot the satellite at this point of time.
    I am calling the SGP4 (a widely used algortithm for satellite orbit propagation).
    That algorithm outputs the vector containing r (satellites coordinates in km), v (satellites velocity)--> but they are in TEME frame, 
    so i will use the function _teme_to_ecef to convert them to ECEF frame. 
    Then the ECEF coordinates are converted to geodetic coordinates (lat, lon, alt) for teh map doing the minimum math.

    --> returns a dictionary with lat, lon, alt_km, vel_kms, timestamp"""

    now = datetime.now(timezone.utc)
    sat = Satrec.twoline2rv(line1, line2)

    # computing the Julian date and fraction for the current time (the time when we want to know the satellite's position)
    jd, fr = jday(now.year, now.month, now.day, now.hour, now.minute, now.second + now.microsecond/1e6)

    error, r, v = sat.sgp4(jd, fr) 
    if error != 0:
        raise ValueError(f"SGP4 error code {error}")

    # converting TEME to ECEF
    x, y, z = _teme_to_ecef(r, v, now)

    # converting ECEF to geodetic coordinates (longitude, latitude, altitude)
    lon, lat, alt = _ecef_to_geodetic.transform(x*1000, y*1000, z*1000)  # meters in -> lon,lat,ellipsoidal height(m)
    # converting altitude to kilometers
    alt_km = alt / 1000.0
    # calculating the velocity magnitude in km/s
    vel_kms = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)

    return {
        "lat": float(lat),
        "lon": float(lon),
        "alt_km": float(alt_km),
        "vel_kms": float(vel_kms),
        "timestamp": now.isoformat(),
    }
