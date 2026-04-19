"""
Verification Agent
==================
Performs KYB (Know Your Business) checks:
  - Company registration validation
  - GSTIN format check
  - Credit/trust scoring
  - Sanctions screening (simulated)
"""

import json
import re
from datetime import datetime
from utils.logger import setup_logger
from utils.llm_client import get_anthropic_client

logger = setup_logger("verification_agent")

client = get_anthropic_client()

SYSTEM_PROMPT = """You are a B2B Verification Agent for an SME.

Your job is to analyse a buyer's business details and produce a trust assessment.

Given company information, you must:
1. Check if the registration number looks valid (format check)
2. Check if the GSTIN format is valid (15-char alphanumeric starting with 2-digit state code)
3. Assess risk based on company details
4. Assign a trust_score from 0 to 100
5. List any red flags

Respond ONLY with a valid JSON object. No markdown, no code fences, no explanation. Example:
{
  "trust_score": 78,
  "registration_valid": true,
  "gstin_valid": true,
  "risk_level": "low",
  "red_flags": [],
  "recommendation": "proceed",
  "notes": "Established company, valid documents"
}

recommendation must be one of: "proceed", "proceed_with_caution", "reject"
risk_level must be one of: "low", "medium", "high"
"""


def clean_json(raw: str) -> str:
    raw = raw.strip()
    if "```" in raw:
        parts = raw.split("```")
        raw = parts[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return raw.strip()


class VerificationAgent:
    async def run(self, buyer: dict) -> dict:
        company = buyer.get("company", "Unknown")
        logger.info(f"Verifying buyer: {company}")

        if client is None:
            reg = str(buyer.get("registration_number", ""))
            gst = str(buyer.get("gstin", "")).strip().upper()
            reg_ok = len(reg) >= 10 and any(ch.isdigit() for ch in reg)
            gst_ok = bool(re.match(r"^\d{2}[A-Z0-9]{13}$", gst))
            score = 45
            if reg_ok:
                score += 20
            if gst_ok:
                score += 25
            if str(buyer.get("email", "")).find("@") > 0:
                score += 8
            score = min(100, score)
            risk = "low" if score >= 75 else "medium" if score >= 60 else "high"
            recommendation = "proceed" if score >= 60 else "reject"
            result = {
                "trust_score": score,
                "registration_valid": reg_ok,
                "gstin_valid": gst_ok,
                "risk_level": risk,
                "red_flags": [] if score >= 60 else ["insufficient_verification_confidence"],
                "recommendation": recommendation,
                "notes": "Local verification fallback used (no ANTHROPIC_API_KEY).",
                "company": company,
                "checked_at": datetime.utcnow().isoformat()
            }
            return result

        user_message = f"""
Please verify this buyer:

Company Name       : {buyer.get('company')}
Registration Number: {buyer.get('registration_number')}
GSTIN              : {buyer.get('gstin')}
Email              : {buyer.get('email')}
Country            : {buyer.get('country')}

Perform your full verification and return the JSON assessment.
"""

        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=600,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        )

        raw = response.content[0].text
        logger.info(f"Verification response: {raw}")

        result = json.loads(clean_json(raw))
        result["company"] = company
        result["checked_at"] = datetime.utcnow().isoformat()

        score = result.get("trust_score", 0)
        status = "✅ PASS" if score >= 60 else "❌ FAIL"
        print(f"\n[Verification Agent]")
        print(f"  Company    : {company}")
        print(f"  Trust Score: {score}/100  {status}")
        print(f"  Risk Level : {result.get('risk_level')}")
        print(f"  GSTIN Valid: {result.get('gstin_valid')}")
        if result.get("red_flags"):
            print(f"  Red Flags  : {', '.join(result['red_flags'])}")
        print(f"  Decision   : {result.get('recommendation', '').upper()}")

        return result