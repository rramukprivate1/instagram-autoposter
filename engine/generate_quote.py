"""
generate_quote.py
Calls Google Gemini API to generate a quote, caption, hashtags,
and background color suggestion based on the selected topic and tone.
"""
import json
import logging
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

genai.configure(api_key=GEMINI_API_KEY)


def build_system_prompt(topic: dict, tone: dict, custom_context: str = "") -> str:
    """Dynamically assembles the AI system prompt from topic, tone, and custom context."""
    context_line = f"\nADDITIONAL CONTEXT FROM ADMIN: {custom_context}" if custom_context else ""
    return f"""You are an Instagram content creator specializing in motivational and life-advice content
for an audience aged 15 to 30.

TOPIC: {topic['name']} — {topic.get('description', '')}
TONE: {tone['name']} — {tone.get('description', '')}{context_line}

Your task:
1. Write ONE original, powerful quote or piece of advice related to the TOPIC above (max 25 words).
2. Write a matching Instagram caption that complements the quote (max 150 characters).
3. Generate exactly 10 relevant Instagram hashtags (without the # symbol).
4. Suggest a background gradient color pair (two hex color codes) that matches the mood of the quote.

IMPORTANT RULES:
- Do NOT copy or directly quote any real, named person or copyrighted source.
- The quote must be 100% original and creative.
- Stay strictly within Instagram Community Guidelines.
- Avoid hate speech, violence, explicit content, or anything that could harm the audience.
- The quote should feel real, relatable, and emotionally resonant for someone aged 15-30.
- Output ONLY valid JSON — no markdown, no explanation. Format:
{{"quote": "...", "caption": "...", "hashtags": ["tag1", "tag2", ...], "bg_from": "#hexcode", "bg_to": "#hexcode"}}"""


def generate_quote(topic: dict, tone: dict, custom_context: str = "") -> dict:
    """
    Calls Gemini API and returns a dict with quote, caption, hashtags, bg_from, bg_to.
    Raises ValueError if parsing fails.
    """
    prompt = build_system_prompt(topic, tone, custom_context)
    logger.info(f"Generating quote for topic='{topic['name']}' tone='{tone['name']}'")

    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        generation_config=genai.GenerationConfig(
            temperature=0.9,
            response_mime_type="application/json",
        )
    )
    response = model.generate_content(prompt)
    raw = response.text.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini response: {raw}")
        raise ValueError(f"Gemini returned invalid JSON: {e}")

    required_keys = {"quote", "caption", "hashtags", "bg_from", "bg_to"}
    if not required_keys.issubset(data.keys()):
        raise ValueError(f"Gemini response missing keys. Got: {list(data.keys())}")

    logger.info(f"Generated quote: {data['quote'][:60]}...")
    return data


def build_series_prompt(topic: dict, tone: dict, slide_count: int, custom_context: str = "") -> str:
    """Assembles the system prompt for a multi-slide carousel post on ONE topic."""
    context_line = f"\nADDITIONAL CONTEXT FROM ADMIN: {custom_context}" if custom_context else ""
    return f"""You are an Instagram content creator specializing in motivational and life-advice content
for an audience aged 15 to 30.

TOPIC: {topic['name']} — {topic.get('description', '')}
TONE: {tone['name']} — {tone.get('description', '')}{context_line}

Your task: create ONE carousel post (a swipeable series of {slide_count} images) that
explores the TOPIC as a connected series - e.g. "{slide_count} signs...", numbered steps,
or a build-up of related short points. This format is popular because carousels are
built for users to swipe through, which is genuinely more engaging content, not a trick
to inflate views - it must stand on its own as useful, honest content.

1. Write exactly {slide_count} slide texts. Each is what appears on ONE image: short,
   punchy, max 18 words, and each must make sense on its own (someone could stop
   swiping after slide 1 and it should still feel complete).
2. Write ONE Instagram caption for the whole post (max 200 characters) that ties the
   series together and gives someone a reason to swipe through all of it.
3. Generate exactly 10 relevant Instagram hashtags (without the # symbol).
4. Suggest a background gradient color pair (two hex color codes) matching the mood.

IMPORTANT RULES:
- Do NOT copy or directly quote any real, named person or copyrighted source.
- All text must be 100% original.
- Stay strictly within Instagram Community Guidelines: no hate speech, violence,
  explicit content, or anything that could harm a 15-30 year old audience.
- No engagement-bait phrasing ("comment X to see more", fake urgency, etc.) - Instagram
  down-ranks this and it isn't the kind of account this is.
- Output ONLY valid JSON — no markdown, no explanation. Format:
{{"slides": ["...", "...", "..."], "caption": "...", "hashtags": ["tag1", "tag2", ...],
"bg_from": "#hexcode", "bg_to": "#hexcode"}}"""


def generate_quote_series(topic: dict, tone: dict, slide_count: int = 4, custom_context: str = "") -> dict:
    """
    Calls Gemini API and returns a dict with slides (list[str]), caption,
    hashtags, bg_from, bg_to - used for carousel/sequence posts.
    Raises ValueError if parsing fails.
    """
    prompt = build_series_prompt(topic, tone, slide_count, custom_context)
    logger.info(f"Generating {slide_count}-slide series for topic='{topic['name']}' tone='{tone['name']}'")

    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        generation_config=genai.GenerationConfig(
            temperature=0.9,
            response_mime_type="application/json",
        )
    )
    response = model.generate_content(prompt)
    raw = response.text.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini series response: {raw}")
        raise ValueError(f"Gemini returned invalid JSON: {e}")

    required_keys = {"slides", "caption", "hashtags", "bg_from", "bg_to"}
    if not required_keys.issubset(data.keys()):
        raise ValueError(f"Gemini series response missing keys. Got: {list(data.keys())}")
    if not isinstance(data["slides"], list) or len(data["slides"]) == 0:
        raise ValueError(f"Gemini series response has no usable slides: {data.get('slides')}")

    logger.info(f"Generated {len(data['slides'])}-slide series, first slide: {data['slides'][0][:50]}...")
    return data


if __name__ == "__main__":
    # Quick test
    test_topic = {"name": "Self Motivation", "description": "Quotes that inspire internal drive and personal growth"}
    test_tone = {
        "name": "Friend",
        "description": "Warm, casual, like advice from a close friend who has been through it",
    }
    result = generate_quote(
        test_topic, test_tone,
        "Make it feel like a late night text from a best friend",
    )
    print(json.dumps(result, indent=2))
