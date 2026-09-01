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


def build_system_prompt(topic: dict, tone: dict, custom_context: str = "", recent_quotes: list = None) -> str:
    """Dynamically assembles the AI system prompt from topic, tone, custom context, and recent output."""
    context_line = f"\nADDITIONAL CONTEXT FROM ADMIN: {custom_context}" if custom_context else ""
    avoid_block = ""
    if recent_quotes:
        recent_list = "\n".join(f'- "{q}"' for q in recent_quotes)
        avoid_block = f"""

RECENTLY POSTED (last several posts, across all topics) - do NOT reuse these opening
phrases, sentence structures, or specific vocabulary. If your first instinct echoes any
of these in wording or shape, choose a genuinely different angle instead:
{recent_list}"""
    return f"""You are a writer creating short-form Instagram text posts for an audience aged 15 to 30.
The visual style is: black background, serif type, left-aligned - closer to a page from someone's
private notebook than a glossy motivational poster. The words need to carry that entirely.

TOPIC: {topic['name']} — {topic.get('description', '')}
TONE: {tone['name']} — {tone.get('description', '')}{context_line}{avoid_block}

Your task:
1. Write ONE original passage related to the TOPIC - structured like a short piece of real
   writing, not a single tidy one-liner:
   - You may open with a short direct-address or hook line ONLY if it genuinely fits - invent
     your own phrasing for it rather than reaching for a familiar or expected opener, and vary
     whether you use one at all from post to post.
   - Then 2-3 short stanzas, each just 1-2 short sentences, building on each other rather than
     restating the same idea.
   - Vary sentence rhythm and structure meaningfully from typical motivational-quote phrasing -
     avoid defaulting to the same handful of sentence shapes every time.
   - Total length under ~55 words so it still reads in a few seconds on a phone.
   - Write it as ONE string with real line breaks: use \\n between lines within a stanza, and
     \\n\\n (a blank line) between stanzas.
2. Write a matching Instagram caption that complements the passage (max 150 characters).
3. Generate exactly 10 relevant Instagram hashtags (without the # symbol).
4. Suggest a background gradient (two hex color codes). Both MUST be near-black - think the
   barest whisper of deep color in almost total darkness (e.g. #0a0a0a to #120a14), never
   bright, pastel, or saturated. The background should be felt more than seen.

IMPORTANT RULES:
- Do NOT copy or directly quote any real, named person or copyrighted source.
- The passage must be 100% original and creative.
- Stay strictly within Instagram Community Guidelines.
- Avoid hate speech, violence, explicit content, or anything that could harm the audience.
- No engagement-bait phrasing ("comment X to get this in your DMs", "like and follow to see
  more", fake urgency, etc.) anywhere in the quote OR caption - Instagram actively down-ranks
  this, and it invites low-quality spam replies instead of real engagement.
- It should feel real, specific, and earned - not a generic template quote.
- Output ONLY valid JSON — no markdown, no explanation. Format:
{{"quote": "line one\\n\\nstanza two line one\\nstanza two line two", "caption": "...",
"hashtags": ["tag1", "tag2", ...], "bg_from": "#hexcode", "bg_to": "#hexcode"}}"""


def generate_quote(topic: dict, tone: dict, custom_context: str = "", recent_quotes: list = None) -> dict:
    """
    Calls Gemini API and returns a dict with quote, caption, hashtags, bg_from, bg_to.
    Raises ValueError if parsing fails.
    """
    prompt = build_system_prompt(topic, tone, custom_context, recent_quotes)
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


def build_series_prompt(
    topic: dict, tone: dict, slide_count: int, custom_context: str = "", recent_quotes: list = None,
) -> str:
    """Assembles the system prompt for a multi-slide carousel post on ONE topic."""
    context_line = f"\nADDITIONAL CONTEXT FROM ADMIN: {custom_context}" if custom_context else ""
    avoid_block = ""
    if recent_quotes:
        recent_list = "\n".join(f'- "{q}"' for q in recent_quotes)
        avoid_block = f"""

RECENTLY POSTED (last several posts, across all topics) - do NOT reuse these opening
phrases, sentence structures, or specific vocabulary. Choose a genuinely different angle:
{recent_list}"""
    return f"""You are an Instagram content creator specializing in motivational and life-advice content
for an audience aged 15 to 30.

TOPIC: {topic['name']} — {topic.get('description', '')}
TONE: {tone['name']} — {tone.get('description', '')}{context_line}{avoid_block}

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
4. Suggest a background gradient (two hex color codes). Both MUST be near-black - think the
   barest whisper of deep color in almost total darkness, never bright, pastel, or saturated.

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


def generate_quote_series(
    topic: dict, tone: dict, slide_count: int = 4, custom_context: str = "", recent_quotes: list = None,
) -> dict:
    """
    Calls Gemini API and returns a dict with slides (list[str]), caption,
    hashtags, bg_from, bg_to - used for carousel/sequence posts.
    Raises ValueError if parsing fails.
    """
    prompt = build_series_prompt(topic, tone, slide_count, custom_context, recent_quotes)
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
