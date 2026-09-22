import uuid
from dotenv import load_dotenv

load_dotenv()

from apps.api.core.db import SessionLocal
from apps.api.models import Brand, KnowledgeChunk, Organization

ORGANIZATION_ID = uuid.UUID("a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d")
ORGANIZATION_NAME = "JA Assure"

BRANDS = [
    {
        "id": uuid.UUID("ea083cec-c84d-41c1-b2c3-0efa21c3e874"),
        "slug": "jade",
        "name": "Jade",
        "description": "Jewellers block insurance for Singapore jewellers and goldsmiths.",
        "voice_description": (
            "Trustworthy, precise, understated luxury — speaks like a specialist who "
            "understands the trade, not a generic insurer."
        ),
        "tone_guidelines": (
            "Confident but never salesy. Avoid hype language and exclamation points. "
            "Lead with risk-specific expertise over generic reassurance."
        ),
        "target_audience": "Independent jewellers, goldsmiths, and jewellery retailers in Singapore.",
        "chunks": [
            ("faq", "What does jewellers block insurance cover?",
             "Jewellers block insurance covers stock, cash, and goods in transit against theft, "
             "fire, and other insured perils across your premises and while in transit."),
            ("faq", "Is coverage available for trade shows?",
             "Yes, temporary coverage extensions are available for goods displayed or transported "
             "to trade shows and exhibitions, subject to declared values."),
            ("approved_claim", "Approved claim framing — coverage scope",
             "You may state that Jade's policy 'covers stock at scheduled premises and in transit', "
             "provided the statement references the current policy schedule."),
            ("approved_claim", "Approved claim framing — transit cover",
             "You may state that Jade 'extends cover to goods in transit between scheduled premises "
             "and approved third-party locations such as trade shows'."),
            ("restricted_claim", "Restricted claim — guaranteed payout",
             "Do not state or imply that claims are 'guaranteed' to be paid, or paid within a fixed "
             "number of days, without the standard underwriting and assessment qualification."),
            ("brand_guideline", "Visual and verbal identity",
             "Jade messaging should evoke precision and craftsmanship; avoid generic insurance stock "
             "imagery and avoid comparing Jade directly to named competitors."),
        ],
    },
    {
        "id": uuid.UUID("f0b48a11-8e92-4f16-89d4-1a91e5e227a1"),
        "slug": "jaguar-transit",
        "name": "Jaguar Transit",
        "description": "High-value goods transit insurance for logistics and freight operators.",
        "voice_description": (
            "Direct, operational, built for logistics professionals who need clarity fast."
        ),
        "tone_guidelines": (
            "Plain language, short sentences, avoid insurance jargon where possible. "
            "Lead with operational outcomes (fewer delays, clear claims process)."
        ),
        "target_audience": "Freight forwarders, logistics operators, and high-value cargo shippers.",
        "chunks": [
            ("faq", "What counts as high-value cargo?",
             "High-value cargo typically includes electronics, pharmaceuticals, precious metals, and "
             "luxury goods above a declared value threshold set in the policy schedule."),
            ("faq", "Do you cover multi-leg international shipments?",
             "Yes, coverage can extend across multiple legs and modes of transport — air, sea, and "
             "land — under a single transit policy."),
            ("approved_claim", "Approved claim framing — coverage scope",
             "You may state that Jaguar Transit 'provides coverage from origin to destination across "
             "air, sea, and land legs' when referencing standard multi-modal policies."),
            ("approved_claim", "Approved claim framing — claims handling",
             "You may state that Jaguar Transit 'offers a dedicated claims process for transit losses', "
             "provided no specific turnaround time is promised."),
            ("restricted_claim", "Restricted claim — zero risk",
             "Do not claim that shipments are 'risk-free', 'loss-proof', or 'fully protected' under "
             "any transit policy — coverage is always subject to policy terms and exclusions."),
            ("brand_guideline", "Visual and verbal identity",
             "Use logistics-forward imagery: ports, warehouses, freight in motion — not generic stock "
             "photography of handshakes or generic office scenes."),
        ],
    },
    {
        "id": uuid.UUID("b2e873f1-4190-4821-bca2-841961e93892"),
        "slug": "doctorshield",
        "name": "DoctorShield",
        "description": "Medical indemnity insurance for doctors and healthcare practitioners in Singapore.",
        "voice_description": (
            "Reassuring, professional, peer-to-peer — speaks doctor to doctor, not insurer to customer."
        ),
        "tone_guidelines": (
            "Empathetic and measured. Never sensationalize malpractice risk. Always align with "
            "Singapore medical advertising and professional conduct norms."
        ),
        "target_audience": "Doctors, specialists, and allied healthcare practitioners in Singapore.",
        "chunks": [
            ("faq", "What does medical indemnity cover?",
             "Medical indemnity insurance covers legal costs and damages arising from claims of "
             "professional negligence in the course of clinical practice."),
            ("faq", "Is coverage retroactive?",
             "Retroactive coverage options are available for claims arising from incidents prior to "
             "the policy start date, subject to underwriting and a specified retroactive date."),
            ("approved_claim", "Approved claim framing — coverage scope",
             "You may state that DoctorShield 'provides indemnity coverage for claims arising from "
             "clinical practice, subject to policy terms'."),
            ("approved_claim", "Approved claim framing — support",
             "You may state that DoctorShield 'offers access to legal support in the event of a claim', "
             "provided no specific outcome or cost figure is promised."),
            ("restricted_claim", "Restricted claim — guaranteed outcome",
             "Do not imply that coverage guarantees a favourable legal outcome, or that claims will "
             "always be settled in the practitioner's favour."),
            ("brand_guideline", "Visual and verbal identity",
             "Use calm, clinical-but-human imagery. Avoid alarming or fear-based messaging about "
             "litigation or malpractice statistics."),
        ],
    },
]


def get_or_create_organization(db) -> Organization:
    org = db.query(Organization).filter_by(name=ORGANIZATION_NAME).first()
    if org is None:
        org = Organization(id=ORGANIZATION_ID, name=ORGANIZATION_NAME)
        db.add(org)
        db.flush()
        print(f"Created organization: {org.name}")
    else:
        print(f"Organization already exists, skipping: {org.name}")
    return org


def seed_with_session(db) -> None:
    org = get_or_create_organization(db)

    for brand_data in BRANDS:
        brand = db.query(Brand).filter((Brand.slug == brand_data["slug"]) | (Brand.id == brand_data["id"])).first()
        if brand is None:
            brand = Brand(
                id=brand_data["id"],
                organization_id=org.id,
                slug=brand_data["slug"],
                name=brand_data["name"],
                description=brand_data["description"],
                voice_description=brand_data["voice_description"],
                tone_guidelines=brand_data["tone_guidelines"],
                target_audience=brand_data["target_audience"],
            )
            db.add(brand)
            db.flush()
            print(f"Created brand: {brand.name}")
        else:
            print(f"Brand already exists, skipping: {brand.name}")

        existing_chunks = db.query(KnowledgeChunk).filter_by(brand_id=brand.id).count()
        if existing_chunks == 0:
            for category, title, content in brand_data["chunks"]:
                db.add(
                    KnowledgeChunk(
                        brand_id=brand.id,
                        category=category,
                        title=title,
                        content=content,
                    )
                )
            print(f"  Inserted {len(brand_data['chunks'])} knowledge chunks for {brand.name}")
        else:
            print(f"  Knowledge chunks already exist for {brand.name} ({existing_chunks}), skipping")

    db.commit()
    print("Seed complete.")


def run() -> None:
    db = SessionLocal()
    try:
        seed_with_session(db)
    finally:
        db.close()


if __name__ == "__main__":
    run()
