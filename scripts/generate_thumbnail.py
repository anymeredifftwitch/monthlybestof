import os
from PIL import Image, ImageDraw, ImageFont

# === PARAMÈTRES ===
ASSETS_DIR = os.path.join("assets")
BACKGROUND_IMAGE_PATH = os.path.join(ASSETS_DIR, "miniature.png")               # ton image de base
OUTPUT_THUMBNAIL_PATH = os.path.join("data", "thumbnail.jpg")

# Coordonnées du texte (exactement 2 points)
X1, Y1 = 80, 120   # Position pour "BEST OF TWITCH"
X2, Y2 = 250, 230  # Position pour le mois (en dessous)

# Police (tu peux mettre un chemin direct ici si tu veux forcer ta police)
FONT_PATH = None  # ex: "C:/Windows/Fonts/arialbd.ttf" ou "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_SIZE_MAIN = 90

# Couleurs
WHITE = (255, 255, 255)
TWITCH_PURPLE = (145, 70, 255)  # #9146ff

# Noms de mois FR (pas de locale requise)
MONTHS_FR = [
    "JANVIER","FÉVRIER","MARS","AVRIL","MAI","JUIN",
    "JUILLET","AOÛT","SEPTEMBRE","OCTOBRE","NOVEMBRE","DÉCEMBRE"
]

def get_current_month_fr_upper():
    from datetime import datetime
    m = datetime.now().month
    return MONTHS_FR[m - 1]

def get_font(size):
    # Si l'utilisateur a fourni un chemin explicite
    if FONT_PATH and os.path.exists(FONT_PATH):
        return ImageFont.truetype(FONT_PATH, size)

    # Sinon, tenter quelques polices connues (avec accents)
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", # Linux
        "C:/Windows/Fonts/arialbd.ttf",                         # Windows
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",    # macOS
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass

    # Dernier recours : police par défaut (⚠️ peut mal gérer certains accents)
    print("⚠️ Aucune police TTF trouvée, fallback sur la police par défaut (accents possibles KO).")
    return ImageFont.load_default()

def draw_text_with_outline(draw, pos, text, font, fill, outline_color, outline_width=4):
    x, y = pos
    # Contour
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    # Remplissage
    draw.text((x, y), text, font=font, fill=fill)

def generate_thumbnail():
    if not os.path.exists(BACKGROUND_IMAGE_PATH):
        print(f"❌ Image de base introuvable : {BACKGROUND_IMAGE_PATH}")
        return

    # S'assurer que le dossier de sortie existe
    os.makedirs(os.path.dirname(OUTPUT_THUMBNAIL_PATH), exist_ok=True)

    # Charger l'image de base
    img = Image.open(BACKGROUND_IMAGE_PATH).convert("RGBA")
    draw = ImageDraw.Draw(img)
    font_main = get_font(FONT_SIZE_MAIN)

    # Textes
    draw_text_with_outline(draw, (X1, Y1), "BEST OF TWITCH", font_main, WHITE, TWITCH_PURPLE, outline_width=4)
    draw_text_with_outline(draw, (X2, Y2), get_current_month_fr_upper(), font_main, WHITE, TWITCH_PURPLE, outline_width=4)

    # Sauvegarde
    img.save(OUTPUT_THUMBNAIL_PATH)
    print(f"✅ Miniature générée : {OUTPUT_THUMBNAIL_PATH}")

if __name__ == "__main__":
    generate_thumbnail()

