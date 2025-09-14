from __future__ import annotations
import httpx
from typing import List, Dict
from satellites.models import TLE

def parse_tle_catalog(text: str) -> List[Dict]:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    records = []
    for i in range(0, len(lines), 3):
        name = lines[i]
        line1 = lines[i+1]
        line2 = lines[i+2]
        norad_id = int(line1[2:7]) 
        records.append({"norad_id": norad_id, "name": name, "line1": line1, "line2": line2})
    return records

async def download_tle_catalog(url: str) -> List[Dict]:
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url)
        r.raise_for_status()
        return parse_tle_catalog(r.text)

def upsert_tles(records: List[Dict]) -> int:
    count = 0
    for r in records:
        TLE.objects.update_or_create(
            norad_id=r["norad_id"],
            defaults={"name": r["name"], "line1": r["line1"], "line2": r["line2"]},
        )
        count += 1
    return count