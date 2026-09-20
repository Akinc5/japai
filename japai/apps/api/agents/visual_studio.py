"""Visual Studio Agent for JAPAI.

Generates:
1. High-fidelity Visual Prompts (Midjourney / DALL-E / Flux) adhering to JA Assure brand guidelines:
   - Jade: Velvet dark aesthetic, macro jewellery, emerald/gold reflections, ultra-high dynamic range.
   - Jaguar Transit: Armoured logistics, biometric air-cargo pods, titanium blue lighting, cinematic scale.
   - DoctorShield: State-of-the-art sterile clinics, warm physician-patient trust, cyan & white daylighting.
2. Structured 5-Slide Carousel breakdowns with visual cues, headline, copy, and call-to-action.
"""

from typing import Any
from sqlalchemy.orm import Session
from apps.api.core import llm_client

BRAND_VISUAL_STYLES = {
    "jade": {
        "palette": "Deep obsidian black, rich emerald green (#0F382C), brushed gold accents",
        "aesthetic": "High-end luxury editorial, macro jewellery photography, dramatic rim lighting, Hasselblad 100MP detail, velvet textures",
        "negative_prompt": "cartoon, cheap, cluttered, watermark, oversaturated plastic, low resolution"
    },
    "jaguar-transit": {
        "palette": "Titanium gray, navy blue (#0A192F), cold laser cyan accents",
        "aesthetic": "Cinematic security documentary, high-tech biometric transit cases, airport tarmac at twilight, armored convoy, sharp industrial photography",
        "negative_prompt": "accident, wreckage, damaged goods, casual couriers, cartoon, blur"
    },
    "doctorshield": {
        "palette": "Clean medical white, clinical cyan (#00A499), warm slate gray",
        "aesthetic": "Modern private medical suite, soft natural daylight, empathetic senior surgeon reviewing digital records, quiet confidence, editorial portraiture",
        "negative_prompt": "blood, gore, distressed patient, sterile laboratory horror, cartoon, messy hospital"
    }
}


def generate_visual_creative(
    brand_slug: str,
    topic: str,
    platform: str,
    db: Session | None = None
) -> dict[str, Any]:
    """Generates visual art prompt and carousel structure."""
    brand_key = brand_slug.lower().replace("_", "-")
    style = BRAND_VISUAL_STYLES.get(brand_key, BRAND_VISUAL_STYLES["jade"])

    prompt = f"""You are an elite creative director for luxury insurance brand '{brand_slug}'.
Topic: {topic}
Target Platform: {platform}
Brand Aesthetic: {style['aesthetic']}
Color Palette: {style['palette']}

Generate a structured JSON response with:
1. "hero_image_prompt": A 3-sentence descriptive text-to-image prompt for Midjourney/Flux. Include camera lens (e.g., 85mm f/1.4), lighting, scene, and mood.
2. "negative_prompt": Filter terms to avoid.
3. "aspect_ratio": Best ratio for {platform} (e.g., "1:1", "16:9", "4:5").
4. "carousel_slides": An array of 5 slide objects, each having:
   - "slide_number": int (1 to 5)
   - "visual_cue": A brief description of the slide graphic or photo
   - "headline": Punchy 4-8 word title
   - "body_copy": 1-2 impactful sentences
   - "cta": Call to action (on slide 5)
"""

    schema = {
        "type": "OBJECT",
        "properties": {
            "hero_image_prompt": {"type": "STRING"},
            "negative_prompt": {"type": "STRING"},
            "aspect_ratio": {"type": "STRING"},
            "carousel_slides": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "slide_number": {"type": "INTEGER"},
                        "visual_cue": {"type": "STRING"},
                        "headline": {"type": "STRING"},
                        "body_copy": {"type": "STRING"},
                        "cta": {"type": "STRING"}
                    },
                    "required": ["slide_number", "visual_cue", "headline", "body_copy"]
                }
            }
        },
        "required": ["hero_image_prompt", "negative_prompt", "aspect_ratio", "carousel_slides"]
    }

    if db:
        try:
            return llm_client.generate_json(
                prompt,
                db,
                schema=schema,
                agent_name="visual_studio",
                required_keys=("hero_image_prompt", "carousel_slides")
            )
        except Exception:
            pass

    # High-quality fallback template
    return {
        "hero_image_prompt": f"Cinematic {style['aesthetic']}, focused on {topic}. Shot on Hasselblad H6D-100c with 85mm f/1.4 lens, dramatic studio rim lighting, moody background in {style['palette']}, ultra-detailed 8k resolution.",
        "negative_prompt": style["negative_prompt"],
        "aspect_ratio": "4:5" if "instagram" in platform.lower() else "16:9",
        "carousel_slides": [
            {
                "slide_number": 1,
                "visual_cue": f"Macro shot representing {topic} with {brand_slug.capitalize()} aesthetic",
                "headline": f"The Hidden Vulnerabilities in {topic}",
                "body_copy": "Standard commercial policies often leave high-value assets exposed at critical junctures.",
                "cta": ""
            },
            {
                "slide_number": 2,
                "visual_cue": "Data breakdown graphic with sleek gold/cyan accents",
                "headline": "Where Standard Policies Fall Short",
                "body_copy": "From transit custody transitions to surgical advisory liabilities, unendorsed coverage caps cause 64% of claims disputes.",
                "cta": ""
            },
            {
                "slide_number": 3,
                "visual_cue": "Side-by-side protection comparison schematic",
                "headline": "Bespoke Underwriting Architecture",
                "body_copy": "Tailored wordings eliminate ambiguous exclusions before your asset leaves the vault or clinic.",
                "cta": ""
            },
            {
                "slide_number": 4,
                "visual_cue": "Close up of certified appraisal and Lloyd's-backed policy seal",
                "headline": "Underwritten for Immediate Liquidity",
                "body_copy": "Direct specialist settlement teams ensure claims resolution in days, not quarters.",
                "cta": ""
            },
            {
                "slide_number": 5,
                "visual_cue": f"Minimalist {brand_slug.capitalize()} branding with consultation card",
                "headline": "Secure Your Specialist Portfolio",
                "body_copy": "Schedule an advisory review with Singapore's premier niche underwriting specialists.",
                "cta": "Link in bio to request confidential risk assessment"
            }
        ]
    }
