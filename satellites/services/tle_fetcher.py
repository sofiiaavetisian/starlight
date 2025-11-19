from __future__ import annotations
import httpx
from typing import List, Dict, Tuple
from datetime import datetime, timedelta, timezone
from satellites.models import TLE

# CelesTrak provides a simple REST endpoint to fetch TLE data by NORAD ID
CELESTRAK_TLE_BY_CATNR = "https://celestrak.org/NORAD/elements/gp.php?CATNR={norad_id}&FORMAT=TLE"

class TLENotFound(Exception):
    pass


def parse_tle_catalog(text: str) -> List[Dict]:
    """Parse a block of text containing one or more TLEs in standard format --> norad id, name, line1, line2"""

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    records = []
    # process lines in groups of three (name, line1, line2)
    for i in range(0, len(lines), 3):
        if i + 2 >= len(lines): break
        name = lines[i]
        line1 = lines[i+1]
        line2 = lines[i+2]
        if not (line1.startswith("1 ") and line2.startswith("2 ")):
            continue
        try:
            norad_id = int(line1[2:7])
        except ValueError:
            continue
        # add the parsed record to the list
        records.append({"norad_id": norad_id, "name": name, "line1": line1, "line2": line2})

    # return the list of parsed TLE records
    return records

def upsert_tles(records: List[Dict]) -> int:

    """Given a list of TLE records (returened from parse_tle_catalog), put them into the database, TLE table."""
    count = 0
    # for each record, update or create the TLE entry
    for r in records:
        TLE.objects.update_or_create(
            norad_id=r["norad_id"],
            defaults={"name": r["name"], "line1": r["line1"], "line2": r["line2"]},
        )
        count += 1

    return count

def fetch_tle_from_celestrak(norad_id: int) -> Tuple[str, str, str]:

    """Little helper that grabs the latest TLE from CelesTrak so I don't have to copy-paste it. 
    I hit their REST endpoint, double-check the response actually looks like a TLE, and
    hand back the name plus the two lines in a tuple."""

    url = CELESTRAK_TLE_BY_CATNR.format(norad_id=norad_id)
    # fetch the TLE data from CelesTrak
    with httpx.Client(timeout=15.0, follow_redirects=True) as client:
        r = client.get(url)
        r.raise_for_status()
        text = r.text.strip()
        if not text:
            raise TLENotFound(f"No TLE returned for {norad_id}")
        recs = parse_tle_catalog(text)
        if not recs:
            raise TLENotFound(f"Unable to parse TLE for {norad_id}")
        # should only be one record for a specific NORAD ID
        rec = recs[0]

        # return the name, line1, line2
        return rec["name"], rec["line1"], rec["line2"]
    

def get_or_refresh_tle(norad_id: int, max_age_hours: int = 48) -> Tuple[str, str, str]:
    """Return a recent TLE for norad_id, fetching from CelesTrak if older than 2 days."""
    tle = TLE.objects.filter(norad_id=norad_id).first()
    now = datetime.now(timezone.utc)
    if tle and tle.updated_at:
        # if the TLE is recent enough, return it, otherwise fetch a new one
        age = now - tle.updated_at.replace(tzinfo=timezone.utc)
        if age < timedelta(hours=max_age_hours):
            return tle.name, tle.line1, tle.line2
        
    # fetch a new TLE from CelesTrak if its too old
    name, l1, l2 = fetch_tle_from_celestrak(norad_id)
    if tle:
        tle.name, tle.line1, tle.line2 = name, l1, l2
        tle.save(update_fields=["name", "line1", "line2", "updated_at"])
    else:
        # add it to the db if none existed before
        TLE.objects.create(norad_id=norad_id, name=name, line1=l1, line2=l2)

    return name, l1, l2
