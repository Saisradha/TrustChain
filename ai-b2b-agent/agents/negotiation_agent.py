"""
Negotiation Agent
==================
Multi-round offer / counter-offer negotiation.
"""

import json
import time
from utils.logger import setup_logger
from utils.llm_client import get_anthropic_client

logger = setup_logger("negotiation_agent")
client = get_anthropic_client()

SYSTEM_PROMPT = """You are a B2B negotiation agent for a seller SME.
Negotiate deals within policy limits. Be commercially smart.
Never go below floor_price. Max discount is max_discount_pct from list_price.
Reply ONLY with a raw JSON object — no markdown, no code fences, no explanation.
Format:
{"action":"counter","our_offer":{"price_per_unit":4500,"quantity":500,"delivery_days":25,"payment_terms":"net_45","total_value":2250000},"justification":"brief reason","round":1}
action must be exactly one of: accept_buyer, counter, deadlock"""


def clean_json(raw: str) -> str:
    raw = raw.strip()
    if "```" in raw:
        parts = raw.split("```")
        raw = parts[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return raw.strip()


class NegotiationAgent:
    async def run(self, rfq: dict, seller_policy: dict) -> dict:
        logger.info("Starting negotiation")

        buyer_rfq = rfq["rfq"]
        max_rounds = seller_policy.get("max_negotiation_rounds", 5)
        current_buyer_price = buyer_rfq["target_price_per_unit"]
        last_our_offer = None
        transcript = []

        print(f"\n[Negotiation Agent]")
        print(f"  Buyer wants : Rs.{buyer_rfq['target_price_per_unit']}/unit, "
              f"{buyer_rfq['delivery_days']}d, {buyer_rfq['payment_terms']}")
        print(f"  Our floor   : Rs.{seller_policy['floor_price_per_unit']}/unit")
        transcript.append({
            "speaker": "buyer",
            "text": (
                f"Need {buyer_rfq['quantity']} units at Rs.{buyer_rfq['target_price_per_unit']}/unit, "
                f"delivery in {buyer_rfq['delivery_days']} days, terms {buyer_rfq['payment_terms']}."
            )
        })

        if client is None:
            buyer_price = int(buyer_rfq["target_price_per_unit"])
            floor = int(seller_policy["floor_price_per_unit"])
            list_price = int(seller_policy.get("list_price_per_unit", floor))
            max_discount_pct = int(seller_policy.get("max_discount_pct", 0))
            min_acceptable = max(floor, int(list_price * (100 - max_discount_pct) / 100))
            agreed = buyer_price if buyer_price >= min_acceptable else min_acceptable
            if agreed > int(list_price * 1.2):
                transcript.append({
                    "speaker": "agent",
                    "text": "Pricing exceeds policy bounds. Escalating to human negotiator."
                })
                return {"status": "escalate_human", "rounds": 1, "transcript": transcript}
            transcript.append({
                "speaker": "agent",
                "text": f"We can close at Rs.{agreed}/unit with the requested terms."
            })
            return {
                "status": "accepted",
                "rounds": 1,
                "transcript": transcript,
                "deal": {
                    "price_per_unit": agreed,
                    "quantity": buyer_rfq["quantity"],
                    "delivery_days": max(buyer_rfq["delivery_days"], seller_policy.get("min_delivery_days", 1)),
                    "payment_terms": buyer_rfq["payment_terms"],
                    "total_value": agreed * buyer_rfq["quantity"],
                    "currency": buyer_rfq.get("currency", "INR"),
                    "product": buyer_rfq["product"]
                }
            }

        for round_num in range(1, max_rounds + 1):
            time.sleep(10)

            prev = f" Last seller offer: {json.dumps(last_our_offer)}." if last_our_offer else " Opening round."
            msg = (
                f"Round {round_num} of {max_rounds}."
                f" Buyer offers Rs.{current_buyer_price}/unit,"
                f" qty={buyer_rfq['quantity']},"
                f" delivery={buyer_rfq['delivery_days']} days,"
                f" terms={buyer_rfq['payment_terms']}."
                f" Seller policy: floor=Rs.{seller_policy['floor_price_per_unit']},"
                f" list=Rs.{seller_policy['list_price_per_unit']},"
                f" max_discount={seller_policy['max_discount_pct']}%,"
                f" min_delivery={seller_policy['min_delivery_days']} days."
                f"{prev}"
                f" Reply with raw JSON only, no markdown."
            )

            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=250,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": msg}]
            )

            raw = response.content[0].text
            logger.info(f"Negotiation raw response: {raw}")

            cleaned = clean_json(raw)
            if not cleaned:
                logger.warning("Empty response from negotiation agent, retrying logic")
                continue

            result = json.loads(cleaned)
            result["round"] = round_num
            last_our_offer = result.get("our_offer", {})

            action = result.get("action", "counter")
            offer = result.get("our_offer", {})
            transcript.append({
                "speaker": "agent",
                "text": result.get("justification", f"Round {round_num}: {action}")
            })

            print(f"\n  Round {round_num}: {action.upper()}")
            if offer:
                print(f"    Offer     : Rs.{offer.get('price_per_unit')}/unit, "
                      f"{offer.get('delivery_days')}d, {offer.get('payment_terms')}")
                print(f"    Rationale : {result.get('justification', '')[:80]}")

            if action == "accept_buyer":
                print(f"\n  Deal accepted on buyer terms!")
                transcript.append({"speaker": "buyer", "text": "Accepted. Please proceed to contract draft."})
                return {
                    "status": "accepted",
                    "rounds": round_num,
                    "transcript": transcript,
                    "deal": {
                        "price_per_unit":  current_buyer_price,
                        "quantity":        buyer_rfq["quantity"],
                        "delivery_days":   buyer_rfq["delivery_days"],
                        "payment_terms":   buyer_rfq["payment_terms"],
                        "total_value":     current_buyer_price * buyer_rfq["quantity"],
                        "currency":        buyer_rfq.get("currency", "INR"),
                        "product":         buyer_rfq["product"]
                    }
                }

            if action == "deadlock":
                transcript.append({
                    "speaker": "buyer",
                    "text": "We cannot align on commercial terms. Escalation requested."
                })
                return {"status": "escalate_human", "rounds": round_num, "transcript": transcript}

            our_price = offer.get("price_per_unit", 9999999)

            # Buyer accepts if our price is within 5% of their target
            if our_price <= current_buyer_price * 1.05:
                print(f"\n  Buyer accepts Rs.{our_price}/unit!")
                transcript.append({"speaker": "buyer", "text": f"Accepted at Rs.{our_price}/unit. Let's close."})
                deal = offer.copy()
                deal["product"]     = buyer_rfq["product"]
                deal["currency"]    = buyer_rfq.get("currency", "INR")
                deal["total_value"] = our_price * buyer_rfq["quantity"]
                return {"status": "accepted", "rounds": round_num, "deal": deal, "transcript": transcript}

            # Buyer nudges price up each round
            current_buyer_price = min(
                current_buyer_price + (round_num * 50),
                our_price - 1
            )

        print(f"\n  Max rounds reached — escalating to human")
        transcript.append({"speaker": "agent", "text": "Max rounds reached. Escalating to human approver."})
        return {"status": "escalate_human", "rounds": max_rounds, "transcript": transcript}