"""
render_image.py
Renders a 1080x1080 Instagram-style quote card using Pillow.
Left-aligned, multi-stanza layout on a near-black background - built to read
like a short piece of real writing, not a generic centered quote template.
"""
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from config import IMAGE_WIDTH, IMAGE_HEIGHT, IMAGE_OUTPUT_DIR

FONT_DIR = Path(__file__).parent / "fonts"
TEXT_COLOR = (236, 232, 222)       # warm ivory, not stark white
LABEL_COLOR = (150, 150, 150)
WATERMARK_COLOR = (110, 110, 110)


def hex_to_rgb(hex_color: str) -> tuple:
    """Convert #RRGGBB string to (R, G, B) tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: tuple) -> str:
    return "#{:02x}{:02x}{:02x}".format(*[max(0, min(255, c)) for c in rgb])


def clamp_to_dark(hex_color: str, max_channel: int = 30) -> str:
    """
    Ensures a color is genuinely near-black regardless of what the AI
    suggested. Without this, the prompt is the only thing preventing a
    bright/saturated "random color theme" background - and prompts get
    ignored sometimes. This scales any too-bright color down proportionally
    so its hue survives faintly instead of being replaced outright.
    """
    r, g, b = hex_to_rgb(hex_color)
    peak = max(r, g, b, 1)
    if peak <= max_channel:
        return hex_color
    scale = max_channel / peak
    return rgb_to_hex((int(r * scale), int(g * scale), int(b * scale)))


def create_gradient_background(width: int, height: int, color_from: str, color_to: str) -> Image.Image:
    """Creates a subtle vertical gradient - both endpoints are pre-clamped near-black."""
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


def get_font(size: int, italic: bool = False):
    """Load Lora (bundled), downloading from Google Fonts' mirror if missing, or falling back."""
    font_file = "Lora-Italic-Variable.ttf" if italic else "Lora-Variable.ttf"
    font_path = FONT_DIR / font_file

    if not font_path.exists():
        filename = "Lora-Italic%5Bwght%5D.ttf" if italic else "Lora%5Bwght%5D.ttf"
        url = f"https://raw.githubusercontent.com/google/fonts/main/ofl/lora/{filename}"
        download_font(url, font_path)

    try:
        return ImageFont.truetype(str(font_path), size)
    except (IOError, OSError) as e:
        print(f"Could not load truetype font: {e}. Falling back to default.")
        return ImageFont.load_default()


def wrap_text_by_width(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list:
    """Pixel-accurate word wrap for one line of text (not character-count based)."""
    words = text.split()
    if not words:
        return []
    lines = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def layout_stanzas(draw: ImageDraw.ImageDraw, text: str, font, max_text_width: int, line_gap: int, stanza_gap: int):
    """Wraps `text` (optionally multi-stanza) at a given font size. Returns (wrapped_stanzas, total_height)."""
    line_h = draw.textbbox((0, 0), "Agjpqy", font=font)[3]
    stanzas = [s.strip() for s in text.split("\n\n") if s.strip()]
    wrapped_stanzas = []
    for stanza in stanzas:
        stanza_lines = []
        for raw_line in stanza.split("\n"):
            stanza_lines.extend(wrap_text_by_width(draw, raw_line, font, max_text_width))
        wrapped_stanzas.append(stanza_lines)

    total_lines = sum(len(s) for s in wrapped_stanzas)
    total_height = (total_lines * (line_h + line_gap)) + (stanza_gap * max(0, len(wrapped_stanzas) - 1))
    return wrapped_stanzas, total_height, line_h


def fit_stanzas(draw: ImageDraw.ImageDraw, text: str, max_text_width: int, max_block_height: int):
    """
    Tries decreasing font sizes until the wrapped text fits max_block_height.
    A ~55-word passage fits comfortably at the starting size, but AI output
    length isn't perfectly reliable - this is what prevents the occasional
    long passage from overflowing off the top/bottom of the card.
    """
    size = 58
    min_size = 34
    line_gap, stanza_gap = 16, 44
    while size >= min_size:
        font = get_font(size)
        wrapped, height, line_h = layout_stanzas(draw, text, font, max_text_width, line_gap, stanza_gap)
        if height <= max_block_height:
            return wrapped, height, line_h, font, line_gap, stanza_gap
        size -= 4
    font = get_font(min_size)
    wrapped, height, line_h = layout_stanzas(draw, text, font, max_text_width, line_gap, stanza_gap)
    return wrapped, height, line_h, font, line_gap, stanza_gap


def render_card(
    text: str,
    bg_from: str = "#0a0a0a",
    bg_to: str = "#12100f",
    output_id: str = "post",
    watermark: str = "",
    slide_label: str = None,
) -> str:
    """
    Generic single-card renderer. Used by render_quote_card() for single
    posts and render_carousel_slides() for each slide of a sequence post.

    `text` may contain multiple stanzas separated by a blank line (\\n\\n) -
    each is wrapped and laid out independently with extra space between
    them, which is what makes this read like short real writing instead of
    one centered block. A single-paragraph string still works fine too.
    Font size auto-shrinks if needed so longer passages never overflow.

    Returns the path to the saved image.
    """
    os.makedirs(IMAGE_OUTPUT_DIR, exist_ok=True)

    bg_from = clamp_to_dark(bg_from)
    bg_to = clamp_to_dark(bg_to)
    img = create_gradient_background(IMAGE_WIDTH, IMAGE_HEIGHT, bg_from, bg_to)
    draw = ImageDraw.Draw(img)

    margin_left = int(IMAGE_WIDTH * 0.12)
    margin_right = int(IMAGE_WIDTH * 0.14)
    max_text_width = IMAGE_WIDTH - margin_left - margin_right
    max_block_height = int(IMAGE_HEIGHT * 0.72)  # leaves room for top/bottom breathing space + watermark

    wrapped_stanzas, total_height, line_h, font, line_gap, stanza_gap = fit_stanzas(
        draw, text, max_text_width, max_block_height
    )

    y = (IMAGE_HEIGHT - total_height) // 2
    for i, stanza_lines in enumerate(wrapped_stanzas):
        for line in stanza_lines:
            draw.text((margin_left, y), line, font=font, fill=TEXT_COLOR)
            y += line_h + line_gap
        if i < len(wrapped_stanzas) - 1:
            y += stanza_gap

    if slide_label:
        label_font = get_font(30, italic=True)
        lbbox = draw.textbbox((0, 0), slide_label, font=label_font)
        lw = lbbox[2] - lbbox[0]
        draw.text((IMAGE_WIDTH - lw - margin_right, 64), slide_label, font=label_font, fill=LABEL_COLOR)

    if watermark:
        wm_font = get_font(26, italic=True)
        draw.text((margin_left, IMAGE_HEIGHT - 68), watermark, font=wm_font, fill=WATERMARK_COLOR)

    output_path = os.path.join(IMAGE_OUTPUT_DIR, f"{output_id}.jpg")
    img = img.convert("RGB")
    img.save(output_path, "JPEG", quality=95)
    return output_path


def render_quote_card(
    quote: str,
    caption: str,
    bg_from: str = "#0a0a0a",
    bg_to: str = "#12100f",
    post_id: str = "post",
    watermark: str = "",
) -> str:
    """Renders a single quote card. `quote` may contain \\n\\n stanza breaks."""
    return render_card(quote, bg_from, bg_to, post_id, watermark)


def render_carousel_slides(
    slides: list,
    bg_from: str = "#0a0a0a",
    bg_to: str = "#12100f",
    post_id: str = "post",
    watermark: str = "",
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
    test_quote = (
        "Man to man:\n\n"
        "If your life is in the gutter, you don't get the luxury of weekends.\n\n"
        "Lock in for 18 hours a day, 7 days a week. Zero distractions, no days off."
    )
    path = render_quote_card(
        quote=test_quote,
        caption="Growth is a choice. Make it today.",
        bg_from="#0a0a0a",
        bg_to="#0a0a0a",
        post_id="test_001",
        watermark="@motivate.daily"
    )
    print(f"Image saved to: {path}")
