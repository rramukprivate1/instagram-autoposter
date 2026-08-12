"""
render_image.py
Renders a 1080x1080 Instagram-style quote card using Pillow.
Supports solid colors, gradients, and custom fonts.
"""
import os
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from config import IMAGE_WIDTH, IMAGE_HEIGHT, IMAGE_OUTPUT_DIR

# Font paths (GitHub Actions Ubuntu runner has these, or we bundle our own)
FONT_DIR = Path(__file__).parent / "fonts"


def hex_to_rgb(hex_color: str) -> tuple:
    """Convert #RRGGBB string to (R, G, B) tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def create_gradient_background(width: int, height: int, color_from: str, color_to: str) -> Image.Image:
    """Creates a vertical gradient image from color_from to color_to."""
    base = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(base)
    r1, g1, b1 = hex_to_rgb(color_from)
    r2, g2, b2 = hex_to_rgb(color_to)
    for y in range(height):
        ratio = y / height
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    return base


def download_font(url: str, dest_path: Path):
    """Downloads a font file from a URL to the destination path."""
    import requests
    try:
        os.makedirs(dest_path.parent, exist_ok=True)
        print(f"Downloading font from {url}...")
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        dest_path.write_bytes(response.content)
        print(f"Successfully downloaded and saved to {dest_path}")
    except Exception as e:
        print(f"Failed to download font: {e}")


def get_font(size: int, bold: bool = False):
    """Load a font from bundled fonts dir, download from Google Fonts if missing, or fall back."""
    font_file = "bold.ttf" if bold else "regular.ttf"
    font_path = FONT_DIR / font_file

    if not font_path.exists():
        # Clean CDN URLs for Roboto static fonts
        url = (
            "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf"
            if bold
            else "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf"
        )
        download_font(url, font_path)

    try:
        return ImageFont.truetype(str(font_path), size)
    except (IOError, OSError) as e:
        print(f"Could not load truetype font: {e}. Falling back to default.")
        return ImageFont.load_default()



def draw_text_centered(
    draw: ImageDraw.ImageDraw,
    text: str,
    font,
    image_width: int,
    y_center: int,
    color: tuple = (255, 255, 255),
    max_chars_per_line: int = 28,
    line_spacing: int = 20,
) -> int:
    """Draws centered wrapped text and returns the bottom y coordinate."""
    lines = textwrap.wrap(text, width=max_chars_per_line)
    total_height = 0
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        lh = bbox[3] - bbox[1]
        line_heights.append((line, lh))
        total_height += lh + line_spacing

    y = y_center - total_height // 2
    for line, lh in line_heights:
        bbox = draw.textbbox((0, 0), line, font=font)
        lw = bbox[2] - bbox[0]
        x = (image_width - lw) // 2
        draw.text((x, y), line, font=font, fill=color)
        y += lh + line_spacing
    return y


def render_card(
    text: str,
    bg_from: str = "#0d0d0d",
    bg_to: str = "#1a1a2e",
    output_id: str = "post",
    watermark: str = "@yourhandle",
    slide_label: str = None,
) -> str:
    """
    Generic single-card renderer. Used directly by render_quote_card() for
    single posts, and by render_carousel_slides() for each slide of a
    sequence post - both share identical visual styling so a carousel
    doesn't look mismatched from a regular post in your feed.
    Returns the path to the saved image.
    """
    os.makedirs(IMAGE_OUTPUT_DIR, exist_ok=True)

    img = create_gradient_background(IMAGE_WIDTH, IMAGE_HEIGHT, bg_from, bg_to)
    draw = ImageDraw.Draw(img)

    # Decorative accent line (top)
    draw.rectangle([80, 120, IMAGE_WIDTH - 80, 123], fill=(255, 255, 255, 100))

    # Main text (large, bold, centered)
    quote_font = get_font(72, bold=True)
    quote_y_center = IMAGE_HEIGHT // 2 - 60
    draw_text_centered(draw, text, quote_font, IMAGE_WIDTH, quote_y_center, color=(255, 255, 255))

    # Decorative accent line (bottom of quote area)
    draw.rectangle([80, IMAGE_HEIGHT - 130, IMAGE_WIDTH - 80, IMAGE_HEIGHT - 127], fill=(255, 255, 255, 100))

    # Watermark / handle (small, bottom center)
    wm_font = get_font(36, bold=False)
    bbox = draw.textbbox((0, 0), watermark, font=wm_font)
    wm_w = bbox[2] - bbox[0]
    draw.text(((IMAGE_WIDTH - wm_w) // 2, IMAGE_HEIGHT - 100), watermark, font=wm_font, fill=(200, 200, 200))

    # Slide indicator for carousels only (e.g. "2 / 5"), small, top-right
    if slide_label:
        label_font = get_font(32, bold=False)
        lbbox = draw.textbbox((0, 0), slide_label, font=label_font)
        lw = lbbox[2] - lbbox[0]
        draw.text((IMAGE_WIDTH - lw - 60, 60), slide_label, font=label_font, fill=(210, 210, 210))

    output_path = os.path.join(IMAGE_OUTPUT_DIR, f"{output_id}.jpg")
    img = img.convert("RGB")
    img.save(output_path, "JPEG", quality=95)
    return output_path


def render_quote_card(
    quote: str,
    caption: str,
    bg_from: str = "#0d0d0d",
    bg_to: str = "#1a1a2e",
    post_id: str = "post",
    watermark: str = "@yourhandle",
) -> str:
    """
    Renders a single 1080x1080 quote card. Unchanged behavior from before -
    existing single-post callers don't need to change.
    """
    return render_card(f"\u201c{quote}\u201d", bg_from, bg_to, post_id, watermark)


def render_carousel_slides(
    slides: list,
    bg_from: str = "#0d0d0d",
    bg_to: str = "#1a1a2e",
    post_id: str = "post",
    watermark: str = "@yourhandle",
) -> list:
    """
    Renders one image per slide of a carousel/sequence post, each labeled
    "n / N" in the corner. Returns the list of file paths in slide order -
    order matters, since publish_post.py uploads and attaches them in this
    same order when building the carousel container.
    """
    total = len(slides)
    paths = []
    for i, slide_text in enumerate(slides, start=1):
        path = render_card(
            slide_text,
            bg_from,
            bg_to,
            output_id=f"{post_id}_slide{i}",
            watermark=watermark,
            slide_label=f"{i} / {total}",
        )
        paths.append(path)
    return paths


if __name__ == "__main__":
    path = render_quote_card(
        quote="Every day you delay is a day you stay the same.",
        caption="Growth is a choice. Make it today.",
        bg_from="#0d0d0d",
        bg_to="#1a0533",
        post_id="test_001",
        watermark="@motivate.daily"
    )
    print(f"Image saved to: {path}")
