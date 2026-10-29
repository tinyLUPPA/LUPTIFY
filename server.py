import os
import re
import time
import json
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import httpx
import yt_dlp
from ytmusicapi import YTMusic

app = FastAPI(title="LUPTIFY Core Audio Engine", version="2.0.0")

# Ensure static directories exist
os.makedirs(os.path.join("static", "css"), exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

http_client = httpx.AsyncClient(
    timeout=15.0,
    limits=httpx.Limits(max_connections=120, max_keepalive_connections=30),
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"}
)

# Initialize YouTube Music API engine
ytmusic = None
try:
    ytmusic = YTMusic()
    print("[LUPTIFY Engine]: YouTube Music API initialized successfully.")
except Exception as e:
    print(f"[LUPTIFY Engine Warning]: YouTube Music API init failed: {e}")

# Stream cache: track_id -> (stream_url, expire_timestamp)
stream_url_cache: Dict[str, Tuple[str, float]] = {}
catalog_cache: Dict[str, Tuple[List[Dict[str, Any]], float]] = {}
CATALOG_CACHE_TTL = 900.0  # 15 minutes TTL for catalog responses
SERVER_START_TIME = time.time()

GENRE_PRESETS = [
    {"id": "pop", "name": "Pop Essentials", "query": "top pop hits 2026", "gradient": "from-rose-500 to-pink-600", "color": "#f43f5e", "icon": "sparkles"},
    {"id": "hiphop", "name": "Hip-Hop & Rap", "query": "hip hop rap hits 2026", "gradient": "from-amber-500 to-orange-600", "color": "#f59e0b", "icon": "flame"},
    {"id": "rock", "name": "Rock & Alternative", "query": "modern rock alternative", "gradient": "from-red-600 to-rose-800", "color": "#dc2626", "icon": "zap"},
    {"id": "lofi", "name": "Lofi Sanctuary", "query": "lofi chill beats study", "gradient": "from-indigo-500 to-purple-600", "color": "#6366f1", "icon": "coffee"},
    {"id": "electronic", "name": "Cyber Club & EDM", "query": "electronic dance synthwave", "gradient": "from-cyan-500 to-blue-600", "color": "#06b6d4", "icon": "disc"},
    {"id": "rnb", "name": "R&B & Soul Vibes", "query": "contemporary rnb soul", "gradient": "from-purple-600 to-pink-500", "color": "#a855f7", "icon": "heart"},
    {"id": "indie", "name": "Indie Escapes", "query": "indie pop rock folk", "gradient": "from-emerald-500 to-teal-600", "color": "#10b981", "icon": "compass"},
    {"id": "jazz", "name": "Midnight Jazz", "query": "smooth jazz classics", "gradient": "from-yellow-600 to-amber-700", "color": "#d97706", "icon": "music"}
]

YT_FEATURED_PLAYLISTS = {
    "PLOHoVaTp8R7dWeCQrKfh7a1a_Gu6KvfWP": {
        "id": "PLOHoVaTp8R7dWeCQrKfh7a1a_Gu6KvfWP",
        "name": "Today's Top Hits 2026",
        "description": "The hottest songs on the planet right now, updated live.",
        "cover": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800&auto=format&fit=crop&q=80",
        "author": "Top Charts"
    },
    "PLDIoUOhQQPlXr63I_vwF9GD8sAKh77dWU": {
        "id": "PLDIoUOhQQPlXr63I_vwF9GD8sAKh77dWU",
        "name": "Global Top Songs 2026",
        "description": "Worldwide streaming hits, chart breakers, and viral anthems.",
        "cover": "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=800&auto=format&fit=crop&q=80",
        "author": "Chillax"
    },
    "PLDIoUOhQQPlXFSnCfj8HuVhOUSC0QwxYD": {
        "id": "PLDIoUOhQQPlXFSnCfj8HuVhOUSC0QwxYD",
        "name": "Hip-Hop & Rap 2026",
        "description": "Hard-hitting bass, cutting-edge flows, and rap essentials.",
        "cover": "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?w=800&auto=format&fit=crop&q=80",
        "author": "Hip-Hop Central"
    },
    "PLfzxR9TEHkQfFPjC1wfveaO1r81gx-6eL": {
        "id": "PLfzxR9TEHkQfFPjC1wfveaO1r81gx-6eL",
        "name": "Chill Lofi Study Beats",
        "description": "Warm tape saturation, peaceful piano, and soothing study vibes.",
        "cover": "https://images.unsplash.com/photo-1518609878373-06d740f60d8b?w=800&auto=format&fit=crop&q=80",
        "author": "Lofi Sanctuary"
    },
    "PLOHoVaTp8R7ccrQM3EpCTVDdwHhXrJhXS": {
        "id": "PLOHoVaTp8R7ccrQM3EpCTVDdwHhXrJhXS",
        "name": "K-Pop Universe 2026",
        "description": "High-octane choreography, infectious hooks, and K-Pop royalty.",
        "cover": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=800&auto=format&fit=crop&q=80",
        "author": "K-Wave"
    },
    "PLpoUYdDxb6P56t8lnxnA412k_H5EMHd-8": {
        "id": "PLpoUYdDxb6P56t8lnxnA412k_H5EMHd-8",
        "name": "Modern Rock & Drive",
        "description": "Electrifying guitars, modern anthems, and alternative fire.",
        "cover": "https://images.unsplash.com/photo-1498038432885-c6f3f1b912ee?w=800&auto=format&fit=crop&q=80",
        "author": "Rock Nation"
    },
    "PL5lj-jZpK0DZRyHZ9v6WpBQRfGSP34c5D": {
        "id": "PL5lj-jZpK0DZRyHZ9v6WpBQRfGSP34c5D",
        "name": "Cyber Club & EDM Party",
        "description": "Peak-time festival bangers, melodic drops, and synth euphoria.",
        "cover": "https://images.unsplash.com/photo-1465847899084-d164df4dedc6?w=800&auto=format&fit=crop&q=80",
        "author": "EDM Party"
    },
    "PLB89694571945E7A6": {
        "id": "PLB89694571945E7A6",
        "name": "Electronic Video Game Remixes",
        "description": "Nostalgic game soundtracks, synth wave tributes, and boss battle beats.",
        "cover": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=800&auto=format&fit=crop&q=80",
        "author": "Game Chiptunes"
    }
}

# Legacy alias for backward compatibility
CURATED_PLAYLISTS = YT_FEATURED_PLAYLISTS

def extract_playlist_id(url_or_id: str) -> str:
    """Extract clean playlist ID from YouTube / YouTube Music URL or raw ID."""
    url_or_id = (url_or_id or "").strip()
    match = re.search(r"[?&]list=([a-zA-Z0-9_-]+)", url_or_id)
    if match:
        return match.group(1)
    clean = url_or_id.split("?")[0].rstrip("/").split("/")[-1]
    return clean

def clean_track_title(title: str) -> str:
    """Strip extraneous noise like (feat. X) or (Official Video) for accurate lyric searching."""
    cleaned = re.sub(r"[\(\[](feat\.|ft\.|official|video|audio|remastered|deluxe|version).*?[\)\]]", "", title, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or title

def format_ytm_track(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Format YouTube Music raw song dictionary into standard LUPTIFY track object."""
    vid = item.get("videoId")
    title = item.get("title")
    if not vid or not title:
        return None
        
    artists_list = item.get("artists", [])
    if isinstance(artists_list, list):
        artist_names = ", ".join([a.get("name", "") for a in artists_list if isinstance(a, dict) and a.get("name")])
    elif isinstance(artists_list, str):
        artist_names = artists_list
    else:
        artist_names = "Unknown Artist"
    if not artist_names:
        artist_names = "Unknown Artist"
        
    album_data = item.get("album")
    album_name = album_data.get("name") if isinstance(album_data, dict) else (str(album_data) if album_data else "")
    
    dur_str = item.get("duration") or item.get("length") or "3:30"
    dur_ms = 210000
    if isinstance(dur_str, str) and ":" in dur_str:
        p = dur_str.split(":")
        try:
            if len(p) == 2:
                dur_ms = (int(p[0]) * 60 + int(p[1])) * 1000
            elif len(p) == 3:
                dur_ms = (int(p[0]) * 3600 + int(p[1]) * 60 + int(p[2])) * 1000
        except Exception:
            pass
    elif item.get("duration_seconds"):
        try:
            dur_ms = int(item["duration_seconds"]) * 1000
        except Exception:
            pass

    thumbs = item.get("thumbnails") or item.get("thumbnail") or []
    cover_url = ""
    if isinstance(thumbs, list) and thumbs:
        raw_url = thumbs[-1].get("url", "")
        if raw_url:
            cover_url = re.sub(r"=w\d+-h\d+.*", "=w600-h600-l90-rj", raw_url)
            cover_url = re.sub(r"=s\d+.*", "=s800", cover_url)
            if not cover_url.startswith("http"):
                cover_url = raw_url
    if not cover_url:
        cover_url = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"

    return {
        "id": vid,
        "name": title,
        "artists": artist_names,
        "album": album_name or "YouTube Music",
        "cover": cover_url,
        "duration_ms": dur_ms,
        "preview_url": None,
        "release_date": str(item.get("year") or "2026"),
        "genre": "Music",
        "video_id": vid
    }

async def fetch_itunes_catalog(query: str, limit: int = 30) -> List[Dict[str, Any]]:
    """Query Apple's open iTunes music catalog for track metadata as fallback."""
    try:
        resp = await http_client.get(
            "https://itunes.apple.com/search",
            params={
                "term": query,
                "media": "music",
                "entity": "song",
                "limit": limit
            }
        )
        if resp.status_code == 200:
            data = resp.json()
            results = []
            for item in data.get("results", []):
                artwork = item.get("artworkUrl100", "")
                if artwork:
                    artwork = re.sub(r"\d+x\d+bb", "600x600bb", artwork)
                else:
                    artwork = "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=600"

                results.append({
                    "id": str(item.get("trackId", "")),
                    "name": item.get("trackName", "Unknown Track"),
                    "artists": item.get("artistName", "Unknown Artist"),
                    "album": item.get("collectionName", "Unknown Album"),
                    "cover": artwork,
                    "duration_ms": item.get("trackTimeMillis", 210000),
                    "preview_url": item.get("previewUrl"),
                    "release_date": item.get("releaseDate", "")[:10],
                    "genre": item.get("primaryGenreName", "Music")
                })
            if results:
                return results
    except Exception as e:
        print(f"[iTunes Catalog Error] query '{query}': {e}")
    return []

async def fetch_dynamic_catalog(query: str, limit: int = 30) -> List[Dict[str, Any]]:
    """Query YouTube Music catalog primarily, with graceful iTunes fallback and memory caching."""
    clean_q = (query or "").strip().lower()
    cache_key = f"{clean_q}__lim{limit}"
    now = time.time()
    
    # Check cache
    if cache_key in catalog_cache:
        cached_tracks, ts = catalog_cache[cache_key]
        if now - ts < CATALOG_CACHE_TTL:
            return cached_tracks

    tracks: List[Dict[str, Any]] = []
    if ytmusic:
        try:
            loop = asyncio.get_running_loop()
            results = await loop.run_in_executor(None, lambda: ytmusic.search(query, filter="songs", limit=limit))
            for item in results:
                formatted = format_ytm_track(item)
                if formatted:
                    tracks.append(formatted)
        except Exception as e:
            print(f"[YTMusic Search Error] query '{query}': {e}")

    if not tracks:
        # Fallback to Apple iTunes catalog
        tracks = await fetch_itunes_catalog(query, limit)

    if tracks:
        catalog_cache[cache_key] = (tracks, now)
        
    return tracks

@app.get("/api/genres")
async def get_genres():
    """Return available genre stations."""
    return {"genres": GENRE_PRESETS}

EXPLORE_QUERIES = {
    "all": "Today's Top Hits 2026",
    "trending": "Viral Hits 2026",
    "tophits": "Billboard Hot 100 2026",
    "chill": "chill lofi beats study relax",
    "relax": "acoustic chill peaceful morning",
    "workout": "high energy gym workout motivation edm",
    "energize": "electronic dance party hits",
    "feel good": "feel good upbeat pop vibes positive",
    "party": "club party dance festival hits",
    "focus": "deep focus study ambient instrumental",
    "commute": "road trip driving anthems pop",
    "romance": "romantic love songs acoustic rnb",
    "hiphop": "hip hop rap essentials 2026",
    "rock": "modern rock alternative indie hits",
    "kpop": "k-pop best hits 2026",
    "anime": "anime openings ost hits",
    "electronic": "cyber synthwave edm club"
}

@app.get("/api/explore")
async def get_explore(category: str = Query("trending"), limit: int = Query(24, ge=1, le=50)):
    """Dynamic mood & category explorer returning real popular tracks."""
    clean_cat = category.lower().strip()
    query = EXPLORE_QUERIES.get(clean_cat, f"{clean_cat} hits 2026")
    tracks = await fetch_dynamic_catalog(query, limit=limit)
    return {
        "category": category,
        "query": query,
        "tracks": tracks
    }

@app.get("/api/home")
async def get_home():
    """Returns curated playlists, genre categories, spotlight, and live trending tracks."""
    # Concurrently fetch top hits and viral charts
    t_hits, t_viral = await asyncio.gather(
        fetch_dynamic_catalog("Today's Top Hits 2026", limit=16),
        fetch_dynamic_catalog("Viral Hits 2026", limit=16),
        return_exceptions=True
    )
    
    hits = t_hits if isinstance(t_hits, list) and t_hits else []
    viral = t_viral if isinstance(t_viral, list) and t_viral else []

    if not hits:
        hits = await fetch_dynamic_catalog("top hits 2026", limit=16)
    if not viral:
        viral = hits[8:] if len(hits) > 8 else hits

    playlists_list = list(YT_FEATURED_PLAYLISTS.values())

    # Spotlight the #1 hottest track
    spotlight = viral[0] if viral else (hits[0] if hits else {
        "id": "spotlight_default",
        "name": "Starboy",
        "artists": "The Weeknd ft. Daft Punk",
        "album": "Starboy",
        "cover": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800",
        "duration_ms": 230000,
        "preview_url": None,
        "genre": "Pop"
    })

    return {
        "spotlight": spotlight,
        "playlists": playlists_list,
        "genres": GENRE_PRESETS,
        "tracks": hits,
        "quick_picks": hits,
        "trending": viral
    }

@app.get("/api/search")
async def search(q: str = Query(..., min_length=1), limit: int = Query(30, ge=1, le=50)):
    """Search tracks, artists, and albums."""
    tracks = await fetch_dynamic_catalog(q, limit=limit)
    return {"tracks": tracks, "query": q}

@app.get("/api/playlist/{playlist_id:path}")
async def get_playlist(playlist_id: str):
    """Retrieve full playlist track list, metadata, and artwork from YouTube Music."""
    clean_id = extract_playlist_id(playlist_id)

    # 1. Check if we can fetch live from YouTube Music
    if ytmusic and (clean_id.startswith("PL") or clean_id.startswith("VLPL") or clean_id.startswith("RD") or clean_id.startswith("OLAK") or len(clean_id) >= 12):
        try:
            loop = asyncio.get_running_loop()
            raw_pl = await loop.run_in_executor(None, lambda: ytmusic.get_playlist(clean_id, limit=100))
            if raw_pl:
                title = raw_pl.get("title") or "YouTube Music Playlist"
                desc = raw_pl.get("description") or ""
                author_data = raw_pl.get("author")
                author_name = author_data.get("name") if isinstance(author_data, dict) else (str(author_data) if author_data else "YouTube Music")

                thumbs = raw_pl.get("thumbnails") or raw_pl.get("thumbnail") or []
                cover_url = ""
                if isinstance(thumbs, list) and thumbs:
                    raw_url = thumbs[-1].get("url", "")
                    if raw_url:
                        cover_url = re.sub(r"=w\d+-h\d+.*", "=w600-h600-l90-rj", raw_url)
                        cover_url = re.sub(r"=s\d+.*", "=s800", cover_url)
                        if not cover_url.startswith("http"):
                            cover_url = raw_url
                if not cover_url and clean_id in YT_FEATURED_PLAYLISTS:
                    cover_url = YT_FEATURED_PLAYLISTS[clean_id]["cover"]
                if not cover_url:
                    cover_url = "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800"

                tracks = []
                for item in raw_pl.get("tracks", []):
                    fmt = format_ytm_track(item)
                    if fmt:
                        tracks.append(fmt)

                return {
                    "id": clean_id,
                    "name": title,
                    "description": desc,
                    "author": author_name,
                    "cover": cover_url,
                    "track_count": raw_pl.get("trackCount", len(tracks)),
                    "tracks": tracks
                }
        except Exception as e:
            print(f"[YTMusic Playlist Fetch Warning] {clean_id}: {e}")

    # 2. Check if clean_id is one of our featured presets
    if clean_id in YT_FEATURED_PLAYLISTS:
        preset = YT_FEATURED_PLAYLISTS[clean_id]
        tracks = await fetch_dynamic_catalog(preset["name"], limit=35)
        return {
            "id": clean_id,
            "name": preset["name"],
            "description": preset["description"],
            "author": preset.get("author", "YouTube Music"),
            "cover": preset["cover"],
            "track_count": len(tracks),
            "tracks": tracks
        }

    # 3. Check if playlist is a genre id
    for g in GENRE_PRESETS:
        if g["id"] == clean_id:
            tracks = await fetch_dynamic_catalog(g["query"], limit=35)
            return {
                "id": g["id"],
                "name": g["name"],
                "description": f"Curated high-fidelity {g['name']} stream.",
                "author": "LUPTIFY Curators",
                "cover": f"https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=800",
                "track_count": len(tracks),
                "tracks": tracks
            }

    # 4. Fallback search by string query
    tracks = await fetch_dynamic_catalog(clean_id, limit=30)
    return {
        "id": clean_id,
        "name": clean_id.capitalize(),
        "description": "Curated collection",
        "author": "YouTube Music",
        "cover": "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=800",
        "track_count": len(tracks),
        "tracks": tracks
    }

@app.get("/api/radio")
async def get_radio(
    artist: str = Query(""),
    track_name: str = Query(""),
    genre: str = Query(""),
    track_id: str = Query("")
):
    """Generate dynamic radio stream recommendations based on YouTube Music Watch Next or artist/genre."""
    tracks: List[Dict[str, Any]] = []

    # 1. Native YouTube Music Watch Playlist / Radio
    target_vid = track_id if (track_id and re.match(r"^[a-zA-Z0-9_-]{10,12}$", track_id)) else None
    if ytmusic and target_vid:
        try:
            loop = asyncio.get_running_loop()
            watch_data = await loop.run_in_executor(None, lambda: ytmusic.get_watch_playlist(videoId=target_vid, limit=25))
            for item in watch_data.get("tracks", []):
                if item.get("videoId") != target_vid:
                    formatted = format_ytm_track(item)
                    if formatted:
                        tracks.append(formatted)
            if tracks:
                return {"tracks": tracks[:25], "seed": {"artist": artist, "track": track_name, "track_id": track_id}}
        except Exception as e:
            print(f"[YTMusic Radio Error]: {e}")

    # 2. Artist & Genre query fallback
    if artist:
        clean_art = clean_track_title(artist)
        artist_tracks = await fetch_dynamic_catalog(f"{clean_art} hits", limit=16)
        tracks.extend(artist_tracks)
        
    vibe = genre or "top hits 2026"
    genre_tracks = await fetch_dynamic_catalog(vibe, limit=16)
    tracks.extend(genre_tracks)
    
    # Deduplicate
    seen = set()
    deduped = []
    for t in tracks:
        tid = t.get("id")
        if tid and tid not in seen:
            seen.add(tid)
            deduped.append(t)
            
    return {
        "tracks": deduped[:25],
        "seed": {"artist": artist, "track": track_name, "genre": genre, "track_id": track_id}
    }

async def translate_lrc_content(lrc_text: str, target_lang: str) -> Optional[str]:
    """Translate LRC lyrics into target language using Google Translate API while preserving timestamps."""
    if not lrc_text or not target_lang or target_lang == "off":
        return None
    try:
        time_re = re.compile(r"^(\[\d{2}:\d{2}\.\d{2,3}\])(.*)$")
        timestamps = []
        texts = []
        for line in lrc_text.strip().split("\n"):
            m = time_re.match(line.strip())
            if m:
                timestamps.append(m.group(1))
                texts.append(m.group(2).strip())
        
        if not texts:
            return None

        resp = await http_client.post(
            f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t",
            data={"q": "\n".join(texts)},
            timeout=7.0
        )
        if resp.status_code == 200:
            parts = resp.json()[0]
            raw_trans = "".join([part[0] for part in parts if part and part[0]])
            trans_lines = [l.strip() for l in raw_trans.split("\n") if l.strip()]
            
            rebuilt = []
            for i in range(len(timestamps)):
                t = timestamps[i]
                trans = trans_lines[i] if i < len(trans_lines) else texts[i]
                rebuilt.append(f"{t} {trans}")
            return "\n".join(rebuilt)
    except Exception as e:
        print(f"[Translation Error]: {e}")
    return None

@app.get("/api/lyrics")
async def get_lyrics(track_name: str, artist_name: str, duration: Optional[int] = None, translate_to: Optional[str] = Query(None)):
    """Fetch synchronized LRC or plain lyrics with intelligent fallback matching and real-time translation."""
    cleaned_name = clean_track_title(track_name)
    cleaned_artist = clean_track_title(artist_name)

    synced_lyrics = None
    plain_lyrics = None
    instrumental = False

    # 1. Direct match on lrclib.net
    params: Dict[str, Any] = {"track_name": cleaned_name, "artist_name": cleaned_artist}
    if duration:
        params["duration"] = duration

    try:
        resp = await http_client.get("https://lrclib.net/api/get", params=params, timeout=6.0)
        if resp.status_code == 200:
            data = resp.json()
            synced_lyrics = data.get("syncedLyrics")
            plain_lyrics = data.get("plainLyrics")
            instrumental = data.get("instrumental", False)
    except Exception:
        pass

    # 2. Fallback search query on lrclib.net
    if not synced_lyrics and not plain_lyrics:
        try:
            search_q = f"{cleaned_artist} {cleaned_name}".strip()
            resp = await http_client.get("https://lrclib.net/api/search", params={"q": search_q}, timeout=6.0)
            if resp.status_code == 200:
                items = resp.json()
                if isinstance(items, list) and items:
                    best = next((x for x in items if x.get("syncedLyrics")), items[0])
                    synced_lyrics = best.get("syncedLyrics")
                    plain_lyrics = best.get("plainLyrics")
                    instrumental = best.get("instrumental", False)
        except Exception:
            pass

    translated_lyrics = None
    if synced_lyrics and translate_to and translate_to != "off":
        translated_lyrics = await translate_lrc_content(synced_lyrics, translate_to)

    return {
        "syncedLyrics": synced_lyrics,
        "translatedLyrics": translated_lyrics,
        "plainLyrics": plain_lyrics or ("Instrumental track or plain lyrics unavailable." if not synced_lyrics else None),
        "instrumental": instrumental,
        "target_lang": translate_to
    }

@app.post("/api/translate")
async def translate_lyrics(payload: Dict[str, Any]):
    """Translate raw lyrics text or LRC into target language on demand."""
    text = payload.get("text", "")
    target_lang = payload.get("target_lang", "id")
    if not text or not target_lang or target_lang == "off":
        return {"translated": text, "target_lang": target_lang}
    
    translated_lrc = await translate_lrc_content(text, target_lang)
    if translated_lrc:
        return {"translated": translated_lrc, "target_lang": target_lang}
    
    # Plain text fallback
    try:
        resp = await http_client.post(
            f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t",
            data={"q": text},
            timeout=7.0
        )
        if resp.status_code == 200:
            parts = resp.json()[0]
            raw_trans = "".join([part[0] for part in parts if part and part[0]])
            return {"translated": raw_trans, "target_lang": target_lang}
    except Exception as e:
        print(f"[Translate API Error]: {e}")
    
    return {"translated": text, "target_lang": target_lang}


def extract_stream_url_sync(query: str, video_id: Optional[str] = None) -> str:
    """Extract YouTube direct audio stream URL using yt_dlp directly from video ID if available, or search query."""
    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "socket_timeout": 10,
    }

    # 1. Direct Video ID extraction (Instant 1.5s bypass!)
    target_urls = []
    if video_id and re.match(r"^[a-zA-Z0-9_-]{10,12}$", video_id):
        target_urls.append(f"https://www.youtube.com/watch?v={video_id}")
    elif re.match(r"^[a-zA-Z0-9_-]{10,12}$", query.strip()):
        target_urls.append(f"https://www.youtube.com/watch?v={query.strip()}")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for u in target_urls:
            try:
                info = ydl.extract_info(u, download=False)
                if info and info.get("url"):
                    return info["url"]
            except Exception as e:
                print(f"[Direct VideoID Error] {u}: {e}")

        # 2. Fallback search queries if video_id not provided or direct fetch failed
        search_queries = [
            f"ytsearch3:{query} official audio",
            f"ytsearch3:{query} audio",
            f"ytsearch3:{query}"
        ]
        for term in search_queries:
            try:
                info = ydl.extract_info(term, download=False)
                if not info:
                    continue
                entries = info.get("entries")
                if entries:
                    for entry in entries:
                        if entry and entry.get("url"):
                            return entry["url"]
                elif info.get("url"):
                    return info["url"]
            except Exception:
                continue
    raise Exception(f"No active audio streams found for '{query}'.")

@app.api_route("/api/stream/{track_id}", methods=["GET", "HEAD"])
async def stream_track(
    track_id: str,
    request: Request,
    name: str = Query(""),
    artist: str = Query(""),
    fallback_url: Optional[str] = Query(None)
):
    """Resolve audio stream URL and proxy audio chunks with HTTP Range seek support."""
    now = time.time()
    direct_url = None

    # Check cache
    cached = stream_url_cache.get(track_id)
    if cached and cached[1] > now:
        direct_url = cached[0]
    else:
        # Resolve via yt_dlp with direct video_id bypass
        video_id = track_id if re.match(r"^[a-zA-Z0-9_-]{10,12}$", track_id) else None
        search_query = f"{artist} {name}".strip() or track_id
        loop = asyncio.get_running_loop()
        try:
            direct_url = await loop.run_in_executor(None, extract_stream_url_sync, search_query, video_id)
            # Store in cache with 30 min expiration
            stream_url_cache[track_id] = (direct_url, now + 1800)
            # Keep cache size bounded
            if len(stream_url_cache) > 250:
                oldest_keys = sorted(stream_url_cache.keys(), key=lambda k: stream_url_cache[k][1])[:50]
                for k in oldest_keys:
                    stream_url_cache.pop(k, None)
        except Exception as e:
            # If YouTube extraction fails, use Apple 30s preview fallback if available
            if fallback_url:
                direct_url = fallback_url
            else:
                try:
                    lookup_res = await http_client.get(f"https://itunes.apple.com/lookup?id={track_id}", timeout=5.0)
                    if lookup_res.status_code == 200:
                        results = lookup_res.json().get("results", [])
                        if results and results[0].get("previewUrl"):
                            direct_url = results[0]["previewUrl"]
                except Exception:
                    pass

            if not direct_url:
                raise HTTPException(status_code=500, detail=f"Stream resolution failed: {str(e)}")

    headers = {}
    if "range" in request.headers:
        headers["Range"] = request.headers["range"]

    try:
        upstream = await http_client.send(
            http_client.build_request("GET", direct_url, headers=headers),
            stream=True
        )
    except Exception as e:
        # If cached link failed, purge and try fallback
        stream_url_cache.pop(track_id, None)
        if fallback_url:
            upstream = await http_client.send(
                http_client.build_request("GET", fallback_url, headers=headers),
                stream=True
            )
        else:
            raise HTTPException(status_code=502, detail=f"Audio proxy connection failed: {e}")

    # If YouTube link returned 403 or 410 (expired URL)
    if upstream.status_code in (403, 410):
        stream_url_cache.pop(track_id, None)
        if fallback_url:
            upstream = await http_client.send(
                http_client.build_request("GET", fallback_url, headers=headers),
                stream=True
            )
        else:
            raise HTTPException(status_code=502, detail="Stream token expired, please replay.")

    resp_headers = {
        "Accept-Ranges": "bytes",
        "Content-Type": upstream.headers.get("Content-Type", "audio/mp4"),
        "Cache-Control": "no-cache",
    }
    if "Content-Length" in upstream.headers:
        resp_headers["Content-Length"] = upstream.headers["Content-Length"]
    if "Content-Range" in upstream.headers:
        resp_headers["Content-Range"] = upstream.headers["Content-Range"]

    if request.method == "HEAD":
        await upstream.aclose()
        return Response(status_code=upstream.status_code, headers=resp_headers)

    async def audio_generator():
        try:
            async for chunk in upstream.aiter_bytes(chunk_size=65536):
                yield chunk
        finally:
            await upstream.aclose()

    return StreamingResponse(
        audio_generator(),
        status_code=upstream.status_code,
        headers=resp_headers
    )

@app.get("/api/proxy_image")
async def proxy_image(url: str = Query(...)):
    """Proxy cover art images with CORS headers so client can cache cover art offline."""
    if not url:
        raise HTTPException(status_code=400, detail="Missing url parameter")
    try:
        resp = await http_client.get(url, timeout=12.0, follow_redirects=True)
        if resp.status_code == 200:
            content_type = resp.headers.get("content-type", "image/jpeg")
            return Response(
                content=resp.content,
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=604800",
                    "Access-Control-Allow-Origin": "*"
                }
            )
        raise HTTPException(status_code=resp.status_code, detail="Failed to fetch image")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image proxy error: {str(e)}")

@app.get("/api/download/{track_id}")
async def download_track_file(
    track_id: str,
    name: str = Query("track"),
    artist: str = Query("artist"),
    fallback_url: Optional[str] = Query(None)
):
    """Direct audio stream file download endpoint with Content-Disposition attachment."""
    now = time.time()
    direct_url = None

    cached = stream_url_cache.get(track_id)
    if cached and cached[1] > now:
        direct_url = cached[0]
    else:
        video_id = track_id if re.match(r"^[a-zA-Z0-9_-]{10,12}$", track_id) else None
        search_query = f"{artist} {name}".strip() or track_id
        loop = asyncio.get_running_loop()
        try:
            direct_url = await loop.run_in_executor(None, extract_stream_url_sync, search_query, video_id)
            stream_url_cache[track_id] = (direct_url, now + 1800)
        except Exception:
            if fallback_url:
                direct_url = fallback_url
            else:
                raise HTTPException(status_code=500, detail="Failed to resolve download stream")

    clean_name = re.sub(r'[\\/*?:"<>|]', "", f"{name} - {artist}").strip() or "track"
    filename = f"{clean_name}.m4a"

    try:
        upstream = await http_client.send(
            http_client.build_request("GET", direct_url),
            stream=True
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Audio proxy connection failed: {e}")

    resp_headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": upstream.headers.get("Content-Type", "audio/mp4"),
        "Accept-Ranges": "bytes"
    }
    if "Content-Length" in upstream.headers:
        resp_headers["Content-Length"] = upstream.headers["Content-Length"]

    async def audio_generator():
        try:
            async for chunk in upstream.aiter_bytes(chunk_size=65536):
                yield chunk
        finally:
            await upstream.aclose()

    return StreamingResponse(
        audio_generator(),
        status_code=upstream.status_code,
        headers=resp_headers
    )


@app.get("/api/status")
async def get_status():
    """Return backend health, uptime, and cache statistics."""
    return {
        "status": "online",
        "engine": "LUPTIFY Core Audio Engine v2.0",
        "uptime_seconds": int(time.time() - SERVER_START_TIME),
        "cached_streams": len(stream_url_cache)
    }

@app.get("/luptify-logo.svg")
async def get_logo():
    """Serve the official LUPTIFY logo."""
    return FileResponse("luptify-logo.svg", media_type="image/svg+xml")

@app.get("/luptify-icon.svg")
async def get_icon():
    """Serve the official LUPTIFY icon."""
    return FileResponse("luptify-icon.svg", media_type="image/svg+xml")

@app.get("/favicon.ico")
async def get_favicon():
    """Serve the official LUPTIFY icon as favicon."""
    return FileResponse("luptify-icon.svg", media_type="image/svg+xml")

@app.get("/styles.css")
@app.get("/static/css/styles.css")
async def serve_root_css():
    """Serve styles.css with no-cache headers so mobile devices always see fresh styles."""
    css_file = os.path.join("static", "css", "styles.css")
    if os.path.exists(css_file):
        return FileResponse(
            css_file, 
            media_type="text/css",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    return Response("", media_type="text/css")

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serve the single-page application UI with no-cache headers."""
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()
    return Response(
        content=content,
        media_type="text/html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)