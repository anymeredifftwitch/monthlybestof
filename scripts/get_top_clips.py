import os
import json
import requests
from datetime import datetime, timedelta, timezone

# ==== PARAMÈTRES ====
CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
if not CLIENT_ID or not CLIENT_SECRET:
    raise RuntimeError("TWITCH_CLIENT_ID et TWITCH_CLIENT_SECRET doivent être configurés.")

AUTH_URL = "https://id.twitch.tv/oauth2/token"
CLIPS_URL = "https://api.twitch.tv/helix/clips"
OUTPUT = os.path.join("data", "top_clips.json")

BROADCASTER_ID = "737048563"  # Anyme023
DAYS_BACK = 30
MIN_VIDEO_DURATION_SECONDS = 850  # Durée minimale totale
MAX_CLIPS_PER_STREAMER = 999      # Limite max de clips

def _as_rfc3339(dt: datetime) -> str:
    # Twitch accepte RFC3339; on force le 'Z' pour l'UTC
    return dt.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

# ==== FONCTIONS ====
def get_token():
    r = requests.post(AUTH_URL, data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    })
    r.raise_for_status()
    return r.json()["access_token"]

def fetch_all_clips(token, start: datetime, end: datetime):
    headers = {"Client-ID": CLIENT_ID, "Authorization": f"Bearer {token}"}
    params = {
        "broadcaster_id": BROADCASTER_ID,
        "started_at": _as_rfc3339(start),
        "ended_at": _as_rfc3339(end),
        "first": 100
    }
    clips = []
    cursor = None

    while True:
        if cursor:
            params["after"] = cursor
        resp = requests.get(CLIPS_URL, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        clips.extend(data.get("data", []))
        cursor = data.get("pagination", {}).get("cursor")
        if not cursor:
            break

    return clips

def filter_by_duration(clips):
    # Tri par vues décroissantes
    clips_sorted = sorted(clips, key=lambda c: c.get("view_count", 0), reverse=True)
    selected = []
    total_duration = 0.0

    for clip in clips_sorted:
        duration = float(clip.get("duration", 0.0))
        if duration > 0:
            selected.append(clip)
            total_duration += duration
        if (total_duration >= MIN_VIDEO_DURATION_SECONDS and len(selected) >= 3) \
           or len(selected) >= MAX_CLIPS_PER_STREAMER:
            break

    return selected, total_duration

# ==== API COMPAT ====
def get_top_clips(access_token=None, num_clips_per_source=50, days_ago=DAYS_BACK):
    """
    Compat avec l'ancien script :
    - ignore num_clips_per_source (on récupère tout via pagination)
    - days_ago remplace DAYS_BACK si fourni
    - retourne la liste sélectionnée
    - écrit toujours dans data/top_clips.json (pour tes autres scripts)
    """
    token = access_token or get_token()
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days_ago)

    all_clips = fetch_all_clips(token, start, end)
    final_clips, total_duration = filter_by_duration(all_clips)

    # S'assurer que le dossier 'data' existe
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(final_clips, f, ensure_ascii=False, indent=2)

    # (Optionnel) Warning si la durée n'atteint pas 850s
    if total_duration < MIN_VIDEO_DURATION_SECONDS and final_clips:
        print(f"⚠️ Durée totale {total_duration:.1f}s < {MIN_VIDEO_DURATION_SECONDS}s (clips disponibles insuffisants).")

    return final_clips

# ==== MAIN ====
def main():
    clips = get_top_clips()
    print(f"✅ {len(clips)} clips sauvegardés dans '{OUTPUT}'.")

if __name__ == "__main__":
    main()
