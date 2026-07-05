import json
from pathlib import Path
from PIL import Image, ImageFilter, ImageDraw, ImageFont


# --- Configuration ---
PARCA_LOGO_PATH = "LOGO_PARCA.png"
WEST_LOGO_PATH = "LOGO_West-Aeterna.png"
IKAC_LOGO_PATH = "LOGO_IKAC.png"
OUTPUT_DIR = "zone_logos"

BLUR_RADIUS = 8

TEXT_FILL = (0, 0, 0)  # simple black
TEXT_STROKE_WIDTH = 0  # no outline/background
TEXT_WIDTH_RATIO = 0.92  # text fills nearly full logo width
STARTING_FONT_SIZE_RATIO = 0.18  # very large starting size

# Example zone list
with open("pleroma/zone_accounts.json", "r") as f:
    zones = json.load(f)


def load_font(size: int):
    font_candidates = [
        Path.home() / ".local/share/fonts/BebasNeue-Regular.ttf",
        "/usr/share/fonts/TTF/DejaVuSansMNerdFont-Bold.ttf",
    ]

    for font_path in font_candidates:
        if Path(font_path).exists():
            return ImageFont.truetype(font_path, size)

    raise FileNotFoundError(
        "No scalable .ttf font found. Please install or provide a .ttf font file."
    )

def fit_text_to_width(draw, text, max_width, starting_size):
    font_size = starting_size

    while font_size > 10:
        font = load_font(font_size+70)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]

        if text_width <= max_width:
            return font

        font_size -= 2

    raise ValueError("Could not fit text to image width.")

def create_zone_logo(zone_name, username):
    # Convert zone name to uppercase
    display_text = zone_name.upper()
    if "(" in zone_name:
        zone_name = display_text[:display_text.find(" (")]
        zone_block = display_text[display_text.find(" (")+1:]
        if zone_block == "(E)":
            logo_path = PARCA_LOGO_PATH
        elif zone_block == "(W)":
            logo_path = WEST_LOGO_PATH
    else: 
        zone_name = display_text 
        zone_block = None
        logo_path = IKAC_LOGO_PATH

    logo = Image.open(logo_path).convert("RGB")

    # Slightly blur the full logo
    blurred_logo = logo.filter(ImageFilter.GaussianBlur(radius=BLUR_RADIUS))

    draw = ImageDraw.Draw(blurred_logo)

    image_width, image_height = blurred_logo.size

    # Make text very large and nearly full width
    max_text_width = int(image_width * TEXT_WIDTH_RATIO)
    starting_font_size = int(image_width * STARTING_FONT_SIZE_RATIO)

    font = fit_text_to_width(
        draw=draw,
        text=zone_name,
        max_width=max_text_width,
        starting_size=starting_font_size,
    )

    # Center text ZONE NAME
    bbox = draw.textbbox((0, 0), zone_name, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (image_width - text_width) / 2
    y = (image_height - text_height) / 2

    # Draw simple black text, no background
    fac = 150 if zone_block else 0
    draw.text(
        (x, y-fac),
        zone_name,
        font=font,
        fill=TEXT_FILL,
    )

    if zone_block:
        # Center text ZONE BLOCK
        bbox = draw.textbbox((0, 0), zone_block, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (image_width - text_width) / 2
        y = (image_height - text_height) / 2

        # Draw simple black text, no background
        draw.text(
            (x, y+150),
            zone_block,
            font=font,
            fill=TEXT_FILL,
        )


    output_path = Path(OUTPUT_DIR) / f"{username}.jpg"
    blurred_logo.save(output_path, "JPEG", quality=95)

    print(f"Saved: {output_path}")


def main():
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    for zone in zones:
        zone_name = zone["fullname"]
        username = zone["username"]

        create_zone_logo(zone_name, username)


if __name__ == "__main__":
    main()
