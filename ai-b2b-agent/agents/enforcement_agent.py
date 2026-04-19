"""
Enforcement Agent
=================
Activates on confirmed SLA breach.
Calculates penalties, drafts breach notices, logs to dispute ledger.
"""

import json
import time
from datetime import datetime
from utils.logger import setup_logger
from utils.llm_client import get_anthropic_client

logger = setup_logger("enforcement_agent")
client = get_anthropic_client()

SYSTEM_PROMPT = """You are a B2B Enforcement Agent for an SME seller.
A delivery breach has occurred. Calculate penalty and draft a breach notice.
PENALTY RULE: 0.5% of total contract value per day of delay, capped at 10%.
Reply ONLY with raw JSON, no markdown, no code fences:
{"penalty_amount":112500,"penalty_pct":2.5,"days_breached":5,"breach_notice":"Dear [Company],\\n\\nThis is formal notice of breach of Contract [ID] dated [date].\\n\\nYour delivery is [N] days overdue per Clause 7. A penalty of Rs.[amount] (0.5% x [N] days x Rs.[total]) is hereby invoked.\\n\\nPlease remit within 3 business days or this matter will be escalated to arbitration.\\n\\nRegards,\\nABC Industrial Supplies","next_steps":["deduct_escrow","send_notice"],"resolution_deadline_days":3,"escalate_to_arbitration":false,"notes":"brief note"}"""


def clean_json(raw: str) -> str:
    raw = raw.strip()
    if "```" in raw:
        parts = raw.split("```")
        raw = parts[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return raw.strip()


class EnforcementAgent:
    async def run(self, context: dict, breach_report: dict) -> dict:
        logger.info("Enforcement agent activated")
        time.sleep(10)

        deal = context.get("deal", {})
        contract = context.get("contract", {})
        total_value = deal.get("total_value", 0)
        days_delayed = breach_report.get("days_delayed", 1)
        buyer = context.get("rfq", {}).get("buyer", {})

        msg = (
            f"Contract ID: {contract.get('contract_id','N/A')}. "
            f"Buyer: {buyer.get('company','Unknown')} ({buyer.get('email','')}). "
            f"Product: {deal.get('product','goods')}. "
            f"Total contract value: Rs.{total_value:,}. "
            f"Breach type: {breach_report.get('delivery_status','delivery_breach')}. "
            f"Days delayed: {days_delayed}. "
            f"Health score: {breach_report.get('health_score',0)}/100. "
            f"Calculate penalty and draft breach notice. Raw JSON only."
        )

        if client is None:
            penalty_pct = min(10.0, 0.5 * float(days_delayed))
            penalty_amount = int((penalty_pct / 100.0) * float(total_value or 0))
            result = {
                "penalty_amount": penalty_amount,
                "penalty_pct": penalty_pct,
                "days_breached": days_delayed,
                "breach_notice": (
                    f"Dear {buyer.get('company', 'Buyer')},\\n\\n"
                    f"This is formal notice of breach of Contract {contract.get('contract_id', 'N/A')}. "
                    f"Delivery is delayed by {days_delayed} day(s). "
                    f"Penalty invoked: Rs.{penalty_amount:,} ({penalty_pct}%).\\n\\n"
                    "Please cure this breach within 3 business days, failing which we will escalate to arbitration.\\n\\n"
                    "Regards,\\nABC Industrial Supplies"
                ),
                "next_steps": ["send_notice", "record_dispute_ledger"],
                "resolution_deadline_days": 3,
                "escalate_to_arbitration": days_delayed > 7,
                "notes": "Local enforcement fallback used (no ANTHROPIC_API_KEY)."
            }
        else:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=600,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": msg}]
            )

            raw = response.content[0].text
            logger.info(f"Enforcement response: {raw}")
            result = json.loads(clean_json(raw))
        result["contract_id"] = contract.get("contract_id")
        result["enforced_at"] = datetime.utcnow().isoformat()

        # Save breach notice
        import os
        os.makedirs("contracts", exist_ok=True)
        notice_file = f"contracts/BREACH-{contract.get('contract_id','UNKNOWN')}.txt"
        with open(notice_file, "w", encoding="utf-8") as f:
            f.write(result.get("breach_notice", ""))

        print(f"\n[Enforcement Agent] BREACH DETECTED")
        print(f"  Contract ID   : {contract.get('contract_id')}")
        print(f"  Days Delayed  : {days_delayed}")
        print(f"  Penalty       : Rs.{result.get('penalty_amount',0):,} ({result.get('penalty_pct',0)}%)")
        print(f"  Next Steps    : {', '.join(result.get('next_steps',[]))}")
        print(f"  Notice saved  : {notice_file}")
        print(f"  Arbitration   : {'Yes' if result.get('escalate_to_arbitration') else 'No'}")

        return result