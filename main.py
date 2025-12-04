import os
import time
from io import BytesIO

import requests
from PIL import Image

# ---------------- CONFIG ----------------

# Which Pokémon IDs to download
START_ID = 1
END_ID = 12  # change to 1025 if you want all of them

# Where to save the processed sprites
DEST_DIR = "processed_sprites"

# DS-style padding / margins (in pixels) AFTER trimming
# Slightly more bottom margin to simulate the "baseline"
MARGINS = {
    "left": 4,
    "right": 4,
    "top": 6,
    "bottom": 10,
}

# PokeAPI GitHub sprite URL pattern
BASE_URL = (
    "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{}.png"
    # For shinies, use:
    # "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/{}.png"
)

# Be nice to the server ♥
DELAY_BETWEEN_REQUESTS = 0.25  # seconds

# ---------------- LOGIC ----------------


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def trim_and_pad(img: Image.Image, margins=MARGINS) -> Image.Image:
    """
    1) Trim all fully transparent space.
    2) Add consistent margins around the cropped sprite.

    This gives a DS-style look: close horizontally, consistent baseline vertically.
    """
    img = img.convert("RGBA")
    alpha = img.split()[-1]  # alpha channel

    bbox = alpha.getbbox()
    # If there's no non-transparent pixel, just return original
    if bbox is None:
        return img

    cropped = img.crop(bbox)

    new_w = cropped.width + margins["left"] + margins["right"]
    new_h = cropped.height + margins["top"] + margins["bottom"]

    # Fully transparent background
    new_img = Image.new("RGBA", (new_w, new_h), (0, 0, 0, 0))

    # Paste cropped sprite with the configured margins
    new_img.paste(cropped, (margins["left"], margins["top"]))

    return new_img


def download_sprite(pokemon_id: int) -> Image.Image | None:
    url = BASE_URL.format(pokemon_id)
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            print(f"[{pokemon_id}] HTTP {resp.status_code}, skipping")
            return None
        return Image.open(BytesIO(resp.content))
    except Exception as e:
        print(f"[{pokemon_id}] Error downloading: {e}")
        return None


def main():
    ensure_dir(DEST_DIR)

    for pid in range(START_ID, END_ID + 1):
        print(f"Processing #{pid}...", end=" ", flush=True)

        img = download_sprite(pid)
        if img is None:
            print("download failed.")
            time.sleep(DELAY_BETWEEN_REQUESTS)
            continue

        processed = trim_and_pad(img)

        out_path = os.path.join(DEST_DIR, f"{pid}.png")
        processed.save(out_path, format="PNG")
        print(f"saved to {out_path}")

        # Be kind to the GitHub/PokeAPI infra
        time.sleep(DELAY_BETWEEN_REQUESTS)


if __name__ == "__main__":
    main()