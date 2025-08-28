import os
import json
import re
import sys
from datetime import datetime

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Scope requis pour l'upload de vidéo
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# --- Paramètres globaux ---
ENABLE_UPLOAD = True  # ⚠️ Mets False pour désactiver l'upload pendant les tests
PLAYLIST_NAME = "BestOfduMois"

# Chemins fichiers
COMPILED_VIDEO_PATH = os.path.join("output", "compiled_video.mp4")
THUMBNAIL_PATH = os.path.join("data", "thumbnail.jpg")
METADATA_JSON_PATH = os.path.join("data", "video_metadata.json")


def upload_video():
    if not ENABLE_UPLOAD:
        print("🚫 Upload désactivé (mode test activé).")
        return False

    print("📤 Démarrage de l'upload YouTube...")

    # Charger les métadonnées
    if not os.path.exists(METADATA_JSON_PATH):
        print(f"❌ Fichier de métadonnées '{METADATA_JSON_PATH}' introuvable.")
        sys.exit(1)

    with open(METADATA_JSON_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    title_from_metadata = metadata["title"]
    description = metadata["description"]
    tags = metadata["tags"]

    # Nettoyage du titre
    cleaned_final_title = re.sub(r'[^\w\s\-\.,\'"!?|]', '', title_from_metadata)
    cleaned_final_title = re.sub(r'!\w+', '', cleaned_final_title)
    cleaned_final_title = re.sub(r'\s+', ' ', cleaned_final_title).strip()

    max_title_length = 100
    if len(cleaned_final_title) > max_title_length:
        truncated_title = cleaned_final_title[:max_title_length - 3].strip()
        last_space = truncated_title.rfind(' ')
        if last_space != -1:
            truncated_title = truncated_title[:last_space]
        cleaned_final_title = truncated_title + "..."

    if not cleaned_final_title:
        cleaned_final_title = "Le meilleur des clips Twitch du Jour"

    title = cleaned_final_title
    category_id = metadata.get("category_id", "20")
    privacy_status = metadata.get("privacyStatus", "public")

    # --- Authentification avec token JSON depuis GitHub Secret ---
    token_json = os.getenv("YOUTUBE_API_TOKEN_JSON")
    if not token_json:
        print("❌ Le secret YOUTUBE_API_TOKEN_JSON n'est pas défini.")
        sys.exit(1)

    creds_data = json.loads(token_json)
    creds = Credentials.from_authorized_user_info(creds_data, scopes=SCOPES)

    # Rafraîchir si nécessaire
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    youtube = build("youtube", "v3", credentials=creds)

    # Vérification vidéo et miniature
    if not os.path.exists(COMPILED_VIDEO_PATH):
        print(f"❌ Vidéo compilée introuvable: {COMPILED_VIDEO_PATH}")
        sys.exit(1)

    thumbnail_present = os.path.exists(THUMBNAIL_PATH)

    # Upload vidéo
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }

    print(f"📤 Upload de la vidéo: '{title}'...")
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=MediaFileUpload(COMPILED_VIDEO_PATH, resumable=True)
    )
    response = request.execute()
    video_id = response["id"]

    # Upload miniature
    if thumbnail_present:
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(THUMBNAIL_PATH)
        ).execute()

    print(f"✅ Vidéo en ligne: https://www.youtube.com/watch?v={video_id}")

    # Ajout dans la playlist
    playlist_id = get_or_create_playlist(youtube, PLAYLIST_NAME)
    youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": video_id
                }
            }
        }
    ).execute()
    print(f"📂 Vidéo ajoutée à la playlist '{PLAYLIST_NAME}'.")

    return True


def get_or_create_playlist(youtube, playlist_name):
    """Récupère l'ID d'une playlist par son nom ou la crée si elle n'existe pas."""
    playlists = youtube.playlists().list(part="snippet", mine=True, maxResults=50).execute()
    for item in playlists.get("items", []):
        if item["snippet"]["title"].lower() == playlist_name.lower():
            return item["id"]

    # Création de la playlist si absente
    new_playlist = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": playlist_name,
                "description": f"Compilation mensuelle {playlist_name}"
            },
            "status": {
                "privacyStatus": "public"
            }
        }
    ).execute()

    return new_playlist["id"]


if __name__ == "__main__":
    upload_video()

