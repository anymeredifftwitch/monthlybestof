import os
import json
from datetime import datetime, timedelta
import locale
import sys  # tu l'utilises pour sys.exit

# --- Chemins des fichiers ---
DOWNLOADED_CLIPS_INFO_JSON = os.path.join("data", "downloaded_clip_paths.json")
OUTPUT_METADATA_JSON = os.path.join("data", "video_metadata.json")

# --- Paramètres de la vidéo YouTube ---
VIDEO_TAGS = ["Anyme023", "BestOf", "Best Of", "Twitch"]

# --- Fonctions utilitaires ---
def format_duration(seconds):
    """Formate une durée en secondes en HH:MM:SS."""
    if seconds < 0:
        seconds = 0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

MONTHS_FR = [
    "JANVIER", "FÉVRIER", "MARS", "AVRIL", "MAI", "JUIN",
    "JUILLET", "AOÛT", "SEPTEMBRE", "OCTOBRE", "NOVEMBRE", "DÉCEMBRE"
]

def get_current_month_fr_upper():
    m = datetime.now().month
    return MONTHS_FR[m - 1]

def generate_metadata():
    print("📝 Génération des métadonnées vidéo (titre, description, tags)...")

    # Tenter de définir la locale pour le français
    try:
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, 'fr_FR')
        except locale.Error:
            print("⚠️ Impossible de définir la locale française pour la date. La date sera en anglais.")

    if not os.path.exists(DOWNLOADED_CLIPS_INFO_JSON):
        print(f"❌ Fichier '{DOWNLOADED_CLIPS_INFO_JSON}' introuvable.")
        default_title = f"Compilation Twitch FR du {datetime.now().strftime('%d/%m/%Y')}"
        with open(OUTPUT_METADATA_JSON, "w", encoding="utf-8") as f:
            json.dump({
                "title": default_title,
                "description": "Aucun clip disponible pour cette compilation.",
                "tags": VIDEO_TAGS
            }, f, ensure_ascii=False, indent=2)
        sys.exit(1)

    with open(DOWNLOADED_CLIPS_INFO_JSON, "r", encoding="utf-8") as f:
        downloaded_clips_info = json.load(f)

    if not downloaded_clips_info:
        print("⚠️ Aucune info de clip téléchargée.")
        default_title = f"Compilation Twitch FR du {datetime.now().strftime('%d/%m/%Y')}"
        with open(OUTPUT_METADATA_JSON, "w", encoding="utf-8") as f:
            json.dump({
                "title": default_title,
                "description": "Aucun clip disponible pour cette compilation.",
                "tags": VIDEO_TAGS
            }, f, ensure_ascii=False, indent=2)
        return

    # --- Construction du titre ---
    current_year = datetime.now().year
    month = get_current_month_fr_upper()
    video_title = f"BEST OF ANYME {month} {current_year} ! LES MEILLEURS MOMENTS DU LIVE TWITCH DE ANYME (BEST OF TWITCH FR) REWIND"

    # --- Description avec chapitres ---
    description_lines = [
        "🎬 Best of Anyme – Les Meilleurs Moments du Stream !",
        "Retrouve dans cette compilation tous les clips les plus drôles, les plus intenses et les plus inattendus de Anyme, le streamer au flow inimitable ! 🔥",
        " ",
        "🕹️ Gameplay, réactions, fails, punchlines... tout est là.",
        "💬 Dis-nous en commentaire ton clip préféré !",
        "📺 Active la cloche 🔔 et abonne-toi pour ne rien rater."
    ]

    current_offset = 0.0
    for clip_info in downloaded_clips_info:
        clip_duration = clip_info.get("duration", 0.0)
        clip_title = clip_info.get("title", "Clip inconnu")
        timecode = format_duration(current_offset)
        description_lines.append(f"{timecode} - {clip_title}")
        current_offset += clip_duration

    description_lines.extend([
        "",
        "Merci d'avoir regardé !",
        "Laissez un like et un commentaire si la vidéo vous a plu.",
        "N'oubliez pas de vous abonner pour plus de contenu !"
    ])

    video_description = "\n".join(description_lines)

    # --- Sauvegarde ---
    os.makedirs(os.path.dirname(OUTPUT_METADATA_JSON), exist_ok=True)
    with open(OUTPUT_METADATA_JSON, "w", encoding="utf-8") as f:
        json.dump({
            "title": video_title,
            "description": video_description,
            "tags": VIDEO_TAGS
        }, f, ensure_ascii=False, indent=2)

    print(f"✅ Métadonnées sauvegardées dans {OUTPUT_METADATA_JSON}")
    print(f"Titre: {video_title}")
    print(f"Description (aperçu):\n{video_description[:500]}...")

if __name__ == "__main__":
    generate_metadata()
