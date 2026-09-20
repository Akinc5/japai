"""Industry Event Calendar & 1-Click Marketing Campaign Trigger for JAPAI.

Manages regional industry events across Singapore & Southeast Asia to trigger
timely, hyper-relevant marketing campaigns across Jade, Jaguar Transit, and DoctorShield.
"""

from datetime import date
from typing import Any

INDUSTRY_EVENTS = [
    {
        "id": "sije-2026",
        "title": "Singapore International Jewelry Expo (SIJE)",
        "brand_slug": "jade",
        "brand_name": "Jade Jewellers Block",
        "target_audience": "Jewellery retailers, gem merchants, exhibition booth holders",
        "location": "Marina Bay Sands Expo & Convention Centre, Singapore",
        "date_window": "July 2026",
        "days_remaining": 45,
        "urgency": "High",
        "suggested_angles": [
            "Exhibition security riders: Why standard shop policies do not cover transit to Marina Bay Sands.",
            "Consignment jewelry perils: Managing unattended display risks during high-footfall expo hours."
        ],
        "default_cta": "Request Express SIJE Exhibition Endorsement"
    },
    {
        "id": "sma-convention-2026",
        "title": "Singapore Medical Association (SMA) Annual Convention",
        "brand_slug": "doctorshield",
        "brand_name": "DoctorShield Medical Indemnity",
        "target_audience": "Private clinic specialists, aesthetic practitioners, surgeons",
        "location": "Suntec Singapore Convention & Exhibition Centre",
        "date_window": "May 2026",
        "days_remaining": 22,
        "urgency": "Critical",
        "suggested_angles": [
            "Navigating revised SMC disciplinary sentencing guidelines & inquiry defense costs.",
            "Tele-consultation liability: Cross-border patient risk management for private clinics."
        ],
        "default_cta": "Schedule Confidential Practice Indemnity Audit"
    },
    {
        "id": "smw-maritime-2026",
        "title": "Singapore Maritime Week & Freight Logistics Summit",
        "brand_slug": "jaguar-transit",
        "brand_name": "Jaguar Transit Cargo Protection",
        "target_audience": "Freight forwarders, high-tech logistics, luxury bullion handlers",
        "location": "Sands Expo & Raffles City Convention Centre",
        "date_window": "April 2026",
        "days_remaining": 14,
        "urgency": "Immediate",
        "suggested_angles": [
            "Red Sea rerouting and extended port dwell times: Protecting high-value electronics and bullion.",
            "Chain of custody transitions: Where freight liability lapses between tarmac and customs vault."
        ],
        "default_cta": "Activate Automated Transit Cover Portal"
    },
    {
        "id": "sg-watch-fair",
        "title": "A Journey Through Time (Singapore Watch Fair)",
        "brand_slug": "jade",
        "brand_name": "Jade Jewellers Block",
        "target_audience": "Haute horlogerie collectors, luxury timepiece boutique owners",
        "location": "Resorts World Sentosa",
        "date_window": "November 2026",
        "days_remaining": 110,
        "urgency": "Medium",
        "suggested_angles": [
            "Vintage watch consignment risk: The appraisal trap in fluctuating secondary watch markets.",
            "Vault storage warranties vs window showcase limits during private VIP viewing events."
        ],
        "default_cta": "Review Horology Block Policy Terms"
    }
]


def get_active_events() -> list[dict[str, Any]]:
    """Return all upcoming industry events."""
    return INDUSTRY_EVENTS


def get_event_by_id(event_id: str) -> dict[str, Any] | None:
    """Find a specific event by ID."""
    for event in INDUSTRY_EVENTS:
        if event["id"] == event_id:
            return event
    return None
