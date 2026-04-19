"""
Monitor Agent
=============
Monitors active transactions for SLA compliance.
In production: polls ERP/logistics APIs every 6 hours.
In this demo: simulates a delivery status check via Claude.
"""

import json
def clean_json(raw):
    raw = raw.strip()
    if "```" in raw:
        parts = raw.split("```")
        raw = parts[1]
        if raw.startswith("json"): raw = raw[4:]
    return raw.strip()
import random
from datetime import datetime, timedelta
from utils.logger import setup_logger
from utils.llm_client import get_anthropic_client

logger = setup_logger("monitor_agent")

client = get_anthropic_client()

SYSTEM_PROMPT = """You are a B2B Transaction Monitor Agent.

Given a transaction context (contract details, deal terms, simulated logistics data),
assess the current health of the transaction.

Check:
1. Is the delivery on track given the contracted delivery_days?
2. Is payment expected on time per payment_terms?
3. Are there any risk signals?

Return ONLY a valid JSON object. No markdown. Example:
{
  "health_score": 85,
  "delivery_status": "on_track",
  "payment_status": "on_track",
  "breach_detected": false,
  "breach_type": null,
  "days_delayed": 0,
  "risk_signals": [],
  "recommendation": "no_action",
  "notes": "Shipment dispatched on day 18, within 25-day window"
}

delivery_status: "on_track" | "at_risk" | "breached"
payment_status: "on_track" | "at_risk" | "overdue"
recommendation: "no_action" | "send_reminder" | "trigger_enforcement"
"""


class MonitorAgent:
    async def run(self, context: dict) -> dict:
        logger.info("Running SLA monitoring check")

        deal = context.get("deal", {})
        contract = context.get("contract", {})

        # Simulate logistics data (in production: call your ERP/TMS API)
        simulated_days_elapsed = random.randint(5, deal.get("delivery_days", 25) + 5)
        simulated_dispatched = simulated_days_elapsed < deal.get("delivery_days", 25)
        simulated_dispatch_day = random.randint(3, min(simulated_days_elapsed, 20))

        user_message = f"""
Monitor this active B2B transaction:

CONTRACT ID     : {contract.get('contract_id', 'N/A')}
PRODUCT         : {deal.get('product')}
QUANTITY        : {deal.get('quantity')} units
CONTRACTED DELIVERY : {deal.get('delivery_days')} days from signing
PAYMENT TERMS   : {deal.get('payment_terms')}
TOTAL VALUE     : ₹{deal.get('total_value', 0):,}

SIMULATED LOGISTICS DATA:
  Days elapsed since contract  : {simulated_days_elapsed}
  Goods dispatched             : {'Yes, on day ' + str(simulated_dispatch_day) if simulated_dispatched else 'Not yet dispatched'}
  Current location             : {'In transit - regional hub' if simulated_dispatched else 'Awaiting dispatch'}

SIMULATED PAYMENT DATA:
  Payment due in               : {deal.get('payment_terms', 'net_30').replace('net_', '')} days from delivery
  Payment received             : No (not yet due)

Assess the transaction health and return your JSON report.
"""

        if client is None:
          delivery_days = int(deal.get("delivery_days", 25))
          delayed = max(0, simulated_days_elapsed - delivery_days)
          breached = delayed > 0 and not simulated_dispatched
          health = 88 if delayed == 0 else max(35, 75 - delayed * 6)
          result = {
            "health_score": health,
            "delivery_status": "on_track" if delayed == 0 else "at_risk" if delayed <= 2 else "breached",
            "payment_status": "on_track",
            "breach_detected": breached,
            "breach_type": "delivery_delay" if breached else None,
            "days_delayed": delayed,
            "risk_signals": [] if delayed == 0 else ["dispatch_delay"],
            "recommendation": "no_action" if delayed == 0 else "send_reminder" if delayed <= 2 else "trigger_enforcement",
            "notes": "Local monitoring fallback used (no ANTHROPIC_API_KEY)."
          }
        else:
          response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
          )

          raw = response.content[0].text.strip()
          result = json.loads(clean_json(raw))
        result["checked_at"] = datetime.utcnow().isoformat()
        result["days_elapsed"] = simulated_days_elapsed

        status_icon = "✅" if result["health_score"] >= 70 else "⚠️" if result["health_score"] >= 50 else "❌"

        print(f"\n[Monitor Agent]")
        print(f"  Health Score    : {result['health_score']}/100  {status_icon}")
        print(f"  Delivery Status : {result['delivery_status']}")
        print(f"  Payment Status  : {result['payment_status']}")
        print(f"  Days Elapsed    : {simulated_days_elapsed}")
        print(f"  Breach Detected : {'❌ YES' if result.get('breach_detected') else '✅ No'}")
        if result.get("risk_signals"):
            print(f"  Risk Signals    : {', '.join(result['risk_signals'])}")
        print(f"  Action          : {result.get('recommendation', 'no_action').upper()}")

        return result