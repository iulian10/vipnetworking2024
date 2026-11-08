#!/usr/bin/env python3
"""Actualizează stats.json cu cifrele publice (YouTube, TikTok, Instagram, Facebook).
Rulează zilnic din GitHub Actions. Dacă o sursă nu răspunde sau dă o cifră suspect de mică, păstrează valoarea veche."""
import json, re, html, subprocess, datetime, urllib.request
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
YT = "UCdw0-0Z3k0pE1vln6fGA9xw"
old = json.load(open("stats.json")); new = dict(old)

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ro,en;q=0.8"})
    return urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "ignore")

def ytdlp(url):
    out = subprocess.run(["yt-dlp", "--flat-playlist", "-J", url], capture_output=True, text=True, timeout=900)
    return json.loads(out.stdout) if out.stdout.strip() else None

def keep(key, val, floor=0.8):
    """Acceptă valoarea nouă doar dacă e plauzibilă (nu scade sub 80% din cea veche)."""
    if isinstance(val, int) and val > 0 and val >= old.get(key, 0) * floor:
        new[key] = val
    else:
        print(f"  păstrez {key}={old.get(key)} (primit: {val})")

# YouTube
try:
    vids = views = 0; subs = None
    for tab in ("videos", "shorts", "streams"):
        d = ytdlp(f"https://www.youtube.com/channel/{YT}/{tab}")
        if not d: raise RuntimeError("yt " + tab)
        E = d.get("entries") or []; vids += len(E); views += sum(e.get("view_count") or 0 for e in E)
        subs = subs or d.get("channel_follower_count")
    keep("yt_subs", subs); keep("yt_videos", vids); keep("yt_views", views)
except Exception as e: print("YouTube:", e)

# TikTok
try:
    s = get("https://www.tiktok.com/@iulipanciu")
    m = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', s, re.S)
    st = json.loads(m.group(1))["__DEFAULT_SCOPE__"]["webapp.user-detail"]["userInfo"]
    st = st.get("statsV2") or st.get("stats")
    keep("tt_followers", int(st["followerCount"])); keep("tt_videos", int(st["videoCount"])); keep("tt_likes", int(st.get("heartCount") or st.get("heart")))
except Exception as e: print("TikTok profil:", e)
try:
    d = ytdlp("https://www.tiktok.com/@iulipanciu")
    if d: keep("tt_views", sum(e.get("view_count") or 0 for e in (d.get("entries") or [])))
except Exception as e: print("TikTok clipuri:", e)

# Instagram (meta: "18K Followers, 527 Following, 664 Posts")
try:
    s = html.unescape(get("https://www.instagram.com/iulipanciu/"))
    m = re.search(r'([\d.,]+)([KkMm]?) Followers, [\d.,]+[KkMm]? Following, ([\d.,]+) Posts', s)
    if m:
        n = float(m.group(1).replace(",", "")); mult = {"k": 1000, "m": 1000000}.get(m.group(2).lower(), 1)
        keep("ig_followers", int(n * mult)); keep("ig_posts", int(m.group(3).replace(",", "")))
except Exception as e: print("Instagram:", e)

# Facebook (meta: "Panciu Iuli. 21.091 urmăritori")
try:
    s = html.unescape(get("https://www.facebook.com/panciu.iuli.1"))
    m = re.search(r'og:description" content="[^"]*?([\d.,]+)\s*(?:urmăritori|followers)', s)
    if m: keep("fb_followers", int(re.sub(r"\D", "", m.group(1))))
except Exception as e: print("Facebook:", e)

if any(new[k] != old.get(k) for k in new if k != "updated"):
    new["updated"] = datetime.date.today().isoformat()
json.dump(new, open("stats.json", "w"), ensure_ascii=False)
print(json.dumps(new, ensure_ascii=False))
