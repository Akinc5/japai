import json
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from apps.api.agents import compliance as compliance_agent
from apps.api.agents import lessons as lessons_agent
from apps.api.core import llm_client
from apps.api.models import Brand, Campaign, ContentAsset, ContentVersion, KnowledgeChunk

MASTERCLASS_TEMPLATES = [
    {
        "id": "jade-jewellers-block-101",
        "brand_slug": "jade",
        "title": "Jewellers Block vs Standard Property Insurance 101",
        "category": "High-Value Specialty Insurance",
        "source_type": "Masterclass Guide",
        "content": """JA Assure Masterclass: Why Standard Commercial Property Fails Jewellers

Most luxury jewellers, diamond merchants, and bespoke goldsmiths in Southeast Asia mistakenly assume their general Commercial All-Risk or Shop Insurance covers their daily operations. 

In reality, standard property policies contain severe exclusionary clauses:
1. Off-Premises & Transit Void: If stones or finished pieces leave the shop for an exhibition (e.g. SIJE), private client viewing, or overseas grading, standard cover terminates immediately.
2. Unattended Display Exclusions: Standard policies require locked safes outside business hours and exclude open-tray snatch theft unless violent force is proven.
3. Consignment & Memo Exposure: Stock received on consignment from international suppliers or sent out on memo is rarely protected under standard fire/theft policies.

Jade Jewellers Block is purpose-built to close these operational gaps:
- True Origin-to-Destination Transit Cover: Protects gems and high-value watches in transit, at exhibitions, and during client viewings across Singapore, Malaysia, Hong Kong, and Thailand.
- Entrusted Goods & Memo Coverage: Full valuation protection for goods in trust, on memo, or with third-party gemmological labs.
- Bespoke Vault & Showcase Deductibles: Tailored security warranty schedules that reflect modern boutique display standards without punitive sub-limits."""
    },
    {
        "id": "doctor-shield-vicarious-liability",
        "brand_slug": "doctor-shield",
        "title": "DoctorShield Masterclass: Clinic Vicarious Liability & Locum Indemnity",
        "category": "Medical Indemnity & Healthcare Risk",
        "source_type": "Whitepaper",
        "content": """DoctorShield Healthcare Risk Report: The Changing Landscape of Medical Indemnity in Singapore

Private clinic operators and specialist medical groups in Singapore face an evolving liability landscape under updated MOH clinical governance guidelines and SMC ethical codes.

Key Areas of Exposure:
1. Vicarious Liability of Clinic Directors: Even if a locum doctor or nurse commits a clinical error, patients and insurers increasingly name the corporate clinic entity in multi-party civil litigation.
2. Locum & Visiting Specialist Gaps: Standard individual MDU/MPS coverage covers the practitioner personally, but leaves clinic assets, administrative staff, and corporate registration vulnerable to third-party claims.
3. Telemedicine & Remote Consultation: The rapid expansion of digital health platforms creates cross-border jurisdiction exposures and consent documentation vulnerabilities.

DoctorShield Corporate Medical Indemnity Solution:
- Seamless Entity & Staff Protection: Bridges the gap between individual practitioner indemnity and corporate clinic liability.
- Medico-Legal Rapid Response: Dedicated specialist legal defence panel experienced in SMC inquiries and Singapore High Court medical proceedings.
- Telemedicine & Multi-Clinic Rider: Unified policy cover extending across physical clinic branches, diagnostic annexes, and registered digital consultation portals."""
    },
    {
        "id": "jaguar-transit-general-average",
        "brand_slug": "ja-assure",
        "title": "Jaguar Transit Masterclass: General Average & Maritime Cargo Vulnerabilities",
        "category": "Supply Chain & Marine Cargo",
        "source_type": "Case Study",
        "content": """Jaguar Transit Supply Chain Briefing: What Every Freight Forwarder Must Know About General Average

When maritime container vessels face emergencies (e.g. fires, groundings, severe storms in the Malacca Strait or South China Sea), vessel captains may declare 'General Average'. 

Under maritime law (York-Antwerp Rules):
1. Shared Sacrifices: All cargo owners on board must proportionately contribute cash deposits to pay for salvage, firefighting, and vessel repair before ANY container is released from port.
2. Uninsured Cargo Held Hostage: If a freight forwarder's customer has no cargo insurance, shipping lines will legally impound the container at the terminal until a six-figure cash bond is posted.
3. Demurrage & Spoilage Accumulation: Cargo sitting under salvage liens incurs massive daily port storage and demurrage fees that often exceed the value of the goods.

Jaguar Transit Integrated Cargo Solution:
- Instant General Average Guarantee Bonds: Insurers immediately post the required salvage guarantees so your containers are released without cash flow delays.
- Multi-Modal Seamless Handover: Continuous protection across sea freight, port handling, air cargo connection, and last-mile land transport under a single scheduled policy."""
    }
]


def get_masterclass_templates() -> List[Dict[str, Any]]:
    return MASTERCLASS_TEMPLATES


def repurpose_document(
    db: Session,
    source_text: str,
    brand_slug: str = "jade",
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Repurposes long-form educational insurance content into a high-converting multi-platform nurture kit."""
    brand = db.query(Brand).filter(Brand.slug == brand_slug).first()
    if not brand:
        # fallback to first brand if slug not found
        brand = db.query(Brand).first()

    # Gather brand context & past lessons
    rules = compliance_agent.get_active_rules(db, brand.id if brand else None)
    rule_summaries = [f"- {r.rule_name}: {r.description}" for r in rules[:8]]
    lessons = lessons_agent.get_recent_lessons(db, brand.id if brand else None, limit=4)
    lessons_text = "\n".join(f"- Avoid past mistake: {l.note or l.reason_tag}" for l in lessons) if lessons else "None"

    system_prompt = f"""You are an expert InsurTech Content Strategist and Growth Copywriter for {brand.name if brand else 'JA Assure'}.
Your task is to take complex, educational insurance source material ("Insurtech 101" / Masterclass / Policy Document) and repurpose it into a comprehensive multi-channel nurture package.

Brand Context:
- Brand Name: {brand.name if brand else 'JA Assure'}
- Voice & Guidelines: {brand.voice_guidelines if brand else 'Authoritative, professional, clear, risk-literate.'}

Mandatory Regulatory Compliance Guardrails:
- Strict adherence to Singapore MAS advertising standards and Insurance Code.
- NEVER make absolute guarantees (e.g. do not say '100% covered', 'instant zero-risk payout', 'never denied').
- Explicitly mention that terms, conditions, and exclusions apply.
- Lessons from past human feedback:
{lessons_text}

Rules to respect:
{chr(10).join(rule_summaries)}

You must return a strictly valid JSON object matching the exact schema specified."""

    user_prompt = f"""Please repurpose the following educational insurance material into 4 distinct marketing formats:

--- SOURCE DOCUMENT ---
{source_text}
-----------------------

Return a JSON object with this exact structure:
{{
  "executive_summary": "2-3 sentence executive synopsis highlighting the critical risk insight.",
  "target_audience": "Specific audience persona (e.g. Luxury Jewellers, Clinic Directors, Freight Forwarders).",
  "key_takeaways": [
    "Takeaway 1 with exact risk exposure",
    "Takeaway 2 with practical solution",
    "Takeaway 3 with compliance note"
  ],
  "linkedin_brief": {{
    "headline": "Punchy LinkedIn hook",
    "body": "4-5 structured paragraphs formatted with clean line breaks. Professional, risk-aware tone with bulleted breakdown and clear CTA.",
    "hashtags": ["#InsurTech", "#RiskManagement", "#Singapore"]
  }},
  "carousel_deck": {{
    "title": "5-Slide Educational Carousel Deck",
    "slides": [
      {{
        "slide_number": 1,
        "role": "Hook & Problem Statement",
        "headline": "Bold Hook Question / Statistic",
        "body": "Short sub-headline that stops the scroll.",
        "visual_direction": "Visual description for graphic designer (e.g. Dark minimalist split layout with high-contrast warning icon)."
      }},
      {{
        "slide_number": 2,
        "role": "The Common Myth",
        "headline": "What 80% of Owners Assume",
        "body": "Explain the standard misconception.",
        "visual_direction": "Visual cue (e.g. Red strike-through over standard policy logo)."
      }},
      {{
        "slide_number": 3,
        "role": "The Real Risk Exposure",
        "headline": "The Hidden Exclusionary Clause",
        "body": "Detail the specific operational vulnerability.",
        "visual_direction": "Visual cue (e.g. Diagram highlighting the transit/exhibition gap)."
      }},
      {{
        "slide_number": 4,
        "role": "The Purpose-Built Solution",
        "headline": "How Modern Cover Solves This",
        "body": "Break down the bespoke coverage structure.",
        "visual_direction": "Visual cue (e.g. Emerald/Gold verified shield checklist)."
      }},
      {{
        "slide_number": 5,
        "role": "Take Action / CTA",
        "headline": "Audit Your Exposure Today",
        "body": "Next steps & policy review consultation call to action.",
        "visual_direction": "Visual cue (e.g. Clean CTA card with brand URL and QR code placeholder)."
      }}
    ]
  }},
  "x_thread": [
    {{
      "post_number": 1,
      "tweet": "Hook tweet under 280 characters opening the thread 🧵"
    }},
    {{
      "post_number": 2,
      "tweet": "Tweet explaining the core hidden risk or gap under 280 characters."
    }},
    {{
      "post_number": 3,
      "tweet": "Tweet explaining the tailored solution under 280 characters."
    }},
    {{
      "post_number": 4,
      "tweet": "Concluding tweet with CTA and compliance disclosure under 280 chars."
    }}
  ],
  "outreach_email": {{
    "subject": "Compelling B2B email subject line",
    "body": "Personalized 3-paragraph cold/warm outreach email addressing the pain point directly and offering a 10-minute risk audit consultation."
  }}
}}"""

    raw_response = llm_client.generate(
        user_prompt,
        db=db,
        system=system_prompt,
        agent_name="repurpose_agent",
        prompt_version="repurpose-v1",
        json_schema=dict,
    )

    try:
        # Extract json safely if wrapped
        cleaned = raw_response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        data = json.loads(cleaned.strip())
    except Exception as e:
        data = {
            "executive_summary": "Extracted risk analysis from masterclass material.",
            "target_audience": "InsurTech Policyholders & Decision Makers",
            "key_takeaways": ["Identify hidden policy exclusions", "Upgrade to specialist cover", "Maintain compliance"],
            "linkedin_brief": {
                "headline": title or "Masterclass Risk Advisory",
                "body": raw_response[:800],
                "hashtags": ["#InsurTech", "#Insurance"]
            },
            "carousel_deck": {
                "title": "Educational Breakdown",
                "slides": [
                    {"slide_number": 1, "role": "Hook", "headline": "Key Risk Insight", "body": "Overview", "visual_direction": "Minimalist graphic"}
                ]
            },
            "x_thread": [{"post_number": 1, "tweet": raw_response[:240]}],
            "outreach_email": {"subject": "Specialist Insurance Advisory", "body": raw_response[:500]}
        }

    # Run compliance verification on the generated LinkedIn copy
    linkedin_copy = data.get("linkedin_brief", {}).get("body", "")
    compliance_result = compliance_agent.run_compliance_check(
        db,
        brand.id if brand else None,
        linkedin_copy
    )

    data["compliance_check"] = {
        "passed": compliance_result.passed if hasattr(compliance_result, "passed") else (compliance_result.outcome == "approved"),
        "outcome": getattr(compliance_result, "outcome", "approved"),
        "issues_found": [issue.model_dump() if hasattr(issue, "model_dump") else issue for issue in getattr(compliance_result, "issues", [])]
    }
    data["brand"] = {
        "id": str(brand.id) if brand else "",
        "name": brand.name if brand else "JA Assure",
        "slug": brand.slug if brand else brand_slug
    }

    return data
