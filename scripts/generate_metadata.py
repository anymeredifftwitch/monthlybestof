import os
import json
from datetime import datetime, timedelta # datetime est déjà importé, mais je le remets pour clarté
import locale # Pour le formatage de la date en français

# --- Chemins des fichiers ---
DOWNLOADED_CLIPS_INFO_JSON = os.path.join("data", "downloaded_clip_paths.json") # Nouvelle source
OUTPUT_METADATA_JSON = os.path.join("data", "video_metadata.json")

# --- Paramètres de la vidéo YouTube ---
# VIDEO_TITLE_PREFIX n'est plus utilisé directement pour le titre principal
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

def generate_metadata():
    print("📝 Génération des métadonnées vidéo (titre, description, tags)...")

    # Tenter de définir la locale pour le français pour le formatage de la date
    try:
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, 'fr_FR') # Essayer sans UTF-8
        except locale.Error:
            print("⚠️ Impossible de définir la locale française pour la date. La date sera en anglais.")


    if not os.path.exists(DOWNLOADED_CLIPS_INFO_JSON):
        print(f"❌ Fichier des informations de clips téléchargés '{DOWNLOADED_CLIPS_INFO_JSON}' introuvable.")
        print("Impossible de générer les métadonnées sans les clips.")
        # Créer un fichier de métadonnées vide pour éviter l'échec des étapes suivantes
        # Le titre par défaut sera plus générique dans ce cas
        default_title = f"Compilation Twitch FR du {datetime.now().strftime('%d/%m/%Y')}"
        with open(OUTPUT_METADATA_JSON, "w", encoding="utf-8") as f:
            json.dump({"title": default_title, "description": "Aucun clip disponible pour cette compilation.", "tags": VIDEO_TAGS}, f, ensure_ascii=False, indent=2)
        sys.exit(1) # Quitte avec une erreur car l'entrée principale manque

    # Charger les informations des clips téléchargés (qui incluent la durée réelle)
    with open(DOWNLOADED_CLIPS_INFO_JSON, "r", encoding="utf-8") as f:
        downloaded_clips_info = json.load(f)

    if not downloaded_clips_info:
        print("⚠️ Aucune information de clip téléchargée disponible pour générer les métadonnées.")
        # Créer un fichier de métadonnées vide
        default_title = f"Compilation Twitch FR du {datetime.now().strftime('%d/%m/%Y')}"
        with open(OUTPUT_METADATA_JSON, "w", encoding="utf-8") as f:
            json.dump({"title": default_title, "description": "Aucun clip disponible pour cette compilation.", "tags": VIDEO_TAGS}, f, ensure_ascii=False, indent=2)
        return # Retourne sans erreur car le fichier est vide, pas manquant

    # --- Construction du titre de la vidéo ---
    # Récupérer le titre du premier clip
    first_clip_title = downloaded_clips_info[0].get("title", "Clips Twitch")
    
    # Formater la date en français
    current_date_fr = datetime.now().strftime("%d %B") # Ex: "03 juillet"
    current_year = datetime.now().year # Pour ajouter l'année si nécessaire

    # Noms de mois FR (pas de locale requise)
    MONTHS_FR = [
    "JANVIER","FÉVRIER","MARS","AVRIL","MAI","JUIN",
    "JUILLET","AOÛT","SEPTEMBRE","OCTOBRE","NOVEMBRE","DÉCEMBRE"
    ]
    month = get_current_month_fr_upper()

    def get_current_month_fr_upper():
        from datetime import datetime
        m = datetime.now().month
        return MONTHS_FR[m - 1]
        # Construction du titre final
        video_title = f"BEST OF ANYME {month} {current_year} ! LES MEILLEURS MOMENTS DU LIVE TWITCH DE ANYME (BEST OF TWITCH FR) REWIND"


    # --- Construction de la description de la vidéo avec chapitres ---
    description_lines = [
        "🎬 Best of Anyme – Les Meilleurs Moments du Stream !",
        "Retrouve dans cette compilation tous les clips les plus drôles, les plus intenses et les plus inattendus de Anyme, le streamer au flow inimitable ! 🔥 Que tu sois un fidèle de ses lives ou que tu le découvres aujourd’hui, ce best of te fera revivre ses moments légendaires.",
        " ",
        "🕹️ Gameplay, réactions, fails, punchlines... tout est là.",
        "💬 Dis-nous en commentaire ton clip préféré !",
        "📺 Active la cloche 🔔 et abonne-toi pour ne rien rater des prochains montages."
    ]

    current_offset = 0.0
    for clip_info in downloaded_clips_info:
        # Utilise la durée réelle du clip stockée dans downloaded_clips_info
        clip_duration = clip_info.get("duration", 0.0)
        
        # Assurez-vous que le titre et le nom du streamer sont disponibles
        clip_title = clip_info.get("title", "Clip inconnu")
        broadcaster_name = clip_info.get("broadcaster_name", "Streamer inconnu")

        # Formatage du timecode et ajout à la description
        timecode = format_duration(current_offset)
        description_lines.append(f"{timecode} - {clip_title}")
        current_offset += clip_duration

    # Ajouter une section de remerciements ou d'appel à l'action
    description_lines.extend([
        "",
        "Merci d'avoir regardé !",
        "Laissez un like et un commentaire si la vidéo vous a plu.",
        "N'oubliez pas de vous abonner pour plus de contenu !"
    ])

    video_description = "\n".join(description_lines)

    # --- Sauvegarde des métadonnées dans un fichier JSON ---
    video_metadata = {
        "title": video_title,
        "description": video_description,
        "tags": VIDEO_TAGS
    }

    output_dir = os.path.dirname(OUTPUT_METADATA_JSON)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(OUTPUT_METADATA_JSON, "w", encoding="utf-8") as f:
        json.dump(video_metadata, f, ensure_ascii=False, indent=2)

    print(f"✅ Métadonnées générées et sauvegardées dans {OUTPUT_METADATA_JSON}.")
    print(f"Titre: {video_title}")
    print(f"Description (extrait):\n{video_description[:500]}...") # Affiche un extrait

if __name__ == "__main__":
    # Importation locale pour main, mais datetime est déjà importé en haut
    # from datetime import datetime # Cette ligne n'est plus nécessaire ici
    generate_metadata()