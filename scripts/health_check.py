#!/usr/bin/env python3
"""Verificare săptămânală a site-ului: HTTPS, certificat, cifre la zi, linkuri. Dacă ceva nu e în regulă, jobul pică și GitHub trimite email."""
import json, ssl, socket, datetime, urllib.request, re, sys
SITE = "vipnetworking2024.com"; UA = {"User-Agent": "Mozilla/5.0 (site health check)"}
problems = []
def get(url, method="GET"):
    req = urllib.request.Request(url, headers=UA, method=method)
    return urllib.request.urlopen(req, timeout=30)
# 1. site răspunde pe HTTPS
try:
    r = get(f"https://{SITE}/"); html = r.read().decode("utf-8", "ignore")
    if r.status != 200: problems.append(f"Site-ul răspunde cu {r.status}")
except Exception as e: problems.append(f"Site-ul nu răspunde: {e}"); html = ""
# 2. certificatul HTTPS nu expiră curând
try:
    ctx = ssl.create_default_context()
    with socket.create_connection((SITE, 443), timeout=20) as s, ctx.wrap_socket(s, server_hostname=SITE) as t:
        exp = datetime.datetime.strptime(t.getpeercert()["notAfter"], "%b %d %H:%M:%S %Y %Z")
    days = (exp - datetime.datetime.now(datetime.UTC).replace(tzinfo=None)).days
    print(f"Certificat valabil încă {days} zile")
    if days < 10: problems.append(f"Certificatul HTTPS expiră în {days} zile")
except Exception as e: problems.append(f"Problemă la certificat: {e}")
# 3. cifrele sunt la zi
try:
    st = json.loads(get(f"https://{SITE}/stats.json").read())
    age = (datetime.date.today() - datetime.date.fromisoformat(st["updated"])).days
    print(f"Cifre actualizate acum {age} zile")
    if age > 5: problems.append(f"Cifrele nu s-au mai actualizat de {age} zile")
except Exception as e: problems.append(f"stats.json lipsă: {e}")
# 4. linkurile externe (clipuri, canale, articole) funcționează
links = sorted(u for u in set(re.findall(r'href="(https://[^"#]+)"', html)) if 'fonts.g' not in u)
bad = []
for u in links:
    try:
        code = get(u, "HEAD").status
    except urllib.error.HTTPError as e:
        code = e.code
        if code in (403, 405, 429): code = 200   # site-uri care refuză roboții, nu linkuri moarte
    except Exception: code = 0
    if code >= 400 or code == 0: bad.append(f"{code} {u}")
print(f"Linkuri verificate: {len(links)}, cu probleme: {len(bad)}")
if bad: problems.append("Linkuri care nu mai merg:\n  " + "\n  ".join(bad))
if problems:
    print("\nPROBLEME:\n- " + "\n- ".join(problems)); sys.exit(1)
print("Totul e în regulă.")
