"""Haalt de agenda's (Airbnb en Natuurhuisje) op en schrijft alleen de bezette nachten
naar availability.json. De iCal-URL's staan in omgevingsvariabelen (GitHub-geheimen),
nooit in de code of de website."""
import json, os, re, sys, urllib.request
from datetime import datetime, timezone, date, timedelta

urls = [u for u in (os.environ.get("ICAL_URL"), os.environ.get("ICAL_URL_NATUURHUISJE")) if u]
if not urls:
    sys.exit("Geen ICAL_URL ingesteld")

def d(v): return date(int(v[:4]), int(v[4:6]), int(v[6:8]))
ranges = []
for url in urls:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    text = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    if "BEGIN:VCALENDAR" not in text:
        sys.exit("Geen geldige agenda ontvangen, bestand niet overschreven")
    text = re.sub(r"\r?\n[ \t]", "", text)
    for ev in text.split("BEGIN:VEVENT")[1:]:
        s = re.search(r"DTSTART[^:]*:(\d{8})", ev)
        e = re.search(r"DTEND[^:]*:(\d{8})", ev)
        if s and e and d(e.group(1)) > d(s.group(1)):
            ranges.append((d(s.group(1)), d(e.group(1))))

ranges.sort()
merged = []
for a, b in ranges:  # overlappende of aansluitende periodes samenvoegen
    if merged and a <= merged[-1][1]:
        merged[-1][1] = max(merged[-1][1], b)
    else:
        merged.append([a, b])
today = date.today()
out = [[a.isoformat(), b.isoformat()] for a, b in merged if b >= today]
json.dump({"updated": datetime.now(timezone.utc).isoformat(timespec="minutes"), "blocked": out},
          open("availability.json", "w"), indent=1)
print(len(out), "periodes opgeslagen")
