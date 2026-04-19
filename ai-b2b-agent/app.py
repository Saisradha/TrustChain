"""
B2B Trust Engine — Flask API Server
=====================================
Run: python app.py
Then open: http://localhost:5000
"""

import asyncio
import json
import uuid
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from orchestrator import Orchestrator
from utils.llm_client import get_anthropic_client

app = Flask(__name__)
orchestrator = Orchestrator()
pitch_client = get_anthropic_client()

# In-memory transaction log for dashboard
transaction_log = []
# In-memory pitch assistant sessions
pitch_chat_sessions = {}


def _fallback_pitch_reply(message: str) -> str:
    msg = (message or "").lower()
    if any(k in msg for k in ["negot", "bargain", "counter", "deal terms"]):
        return (
            "For negotiation, use a policy-first flow: set floor price, delivery minimum, and payment constraints first. "
            "Then run round-based counteroffers with clear guardrails and auto-escalate when no overlap exists after max rounds. "
            "This keeps deals fast while protecting margins."
        )
    if any(k in msg for k in ["price", "pricing", "cost"]):
        return (
            "TrustChain is modular: core transaction automation, negotiation intelligence, "
            "and enforcement can be adopted in phases. Typical ROI comes from faster deal closure "
            "and lower manual operations in procurement workflows."
        )
    if any(k in msg for k in ["security", "safe", "compliance", "data"]):
        return (
            "Security is handled through policy-guarded negotiation, auditable logs per transaction, "
            "and contract traceability. You can also integrate your own auth, storage, and compliance controls."
        )
    if any(k in msg for k in ["integrat", "erp", "sap", "api"]):
        return (
            "TrustChain can integrate with ERP and logistics APIs via orchestrator hooks. "
            "A common rollout starts with RFQ and contract generation, then adds monitoring and enforcement feeds."
        )
    if any(k in msg for k in ["benefit", "why", "value", "advantage"]):
        return (
            "Key value: pre-deal risk checks, faster negotiation cycles, instant contract generation, "
            "SLA monitoring, and automated enforcement steps. This reduces cycle time and dispute leakage."
        )
    return (
        "Great question. TrustChain helps teams verify counterparties, negotiate within policy, "
        "generate legal contracts instantly, monitor delivery health, and auto-initiate enforcement on breach. "
        "Ask me about pricing, integration, rollout strategy, or security."
    )


def _get_pitch_reply(session_id: str, user_message: str):
    history = pitch_chat_sessions.setdefault(session_id, [])
    history.append({"role": "user", "text": user_message})
    context_lines = [f"{m['role']}: {m['text']}" for m in history[-10:]]
    context_blob = "\n".join(context_lines)

    if pitch_client is None:
        reply = _fallback_pitch_reply(user_message)
        history.append({"role": "assistant", "text": reply})
        return reply, "fallback"

    try:
        response = pitch_client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=280,
            system=(
                "You are TrustChain's product assistant. "
                "Answer user doubts in clear business language. "
                "Keep each response concise (2-4 sentences), practical, and factual. "
                "Use conversation context to answer follow-up questions consistently."
            ),
            messages=[{
                "role": "user",
                "content": (
                    f"Conversation context:\n{context_blob}\n\n"
                    f"Latest user question: {user_message}"
                )
            }]
        )
        reply = response.content[0].text.strip()
        history.append({"role": "assistant", "text": reply})
        return reply, "llm"
    except Exception:
        reply = _fallback_pitch_reply(user_message)
        history.append({"role": "assistant", "text": reply})
        return reply, "fallback"


@app.route("/api/pitch-chat", methods=["POST"])
def pitch_chat():
    data = request.json or {}
    session_id = str(data.get("session_id") or "").strip() or f"PITCH-{uuid.uuid4().hex[:10].upper()}"
    user_message = str(data.get("message", "")).strip()
    if not user_message:
        return jsonify({"status": "error", "message": "Message is required"}), 400

    reply, mode = _get_pitch_reply(session_id, user_message)
    return jsonify({"status": "ok", "reply": reply, "mode": mode, "session_id": session_id})


@app.route("/api/pitch-chat-stream", methods=["POST"])
def pitch_chat_stream():
    data = request.json or {}
    session_id = str(data.get("session_id") or "").strip() or f"PITCH-{uuid.uuid4().hex[:10].upper()}"
    user_message = str(data.get("message", "")).strip()
    if not user_message:
        return jsonify({"status": "error", "message": "Message is required"}), 400

    reply, mode = _get_pitch_reply(session_id, user_message)

    def generate():
        meta = json.dumps({"type": "meta", "session_id": session_id, "mode": mode})
        yield f"data: {meta}\n\n"

        words = reply.split(" ")
        built = ""
        for w in words:
            built = (built + " " + w).strip()
            chunk = json.dumps({"type": "chunk", "text": built})
            yield f"data: {chunk}\n\n"
            time.sleep(0.03)

        done = json.dumps({"type": "done"})
        yield f"data: {done}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/run", methods=["POST"])
def run_transaction():
    data = request.json

    txn_id = f"TXN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:4].upper()}"

    rfq = {
        "transaction_id": txn_id,
        "type": "purchase_order",
        "buyer": {
            "company":             data.get("company", "Demo Buyer Ltd"),
            "registration_number": data.get("reg_number", "U74999MH2010PTC123456"),
            "gstin":               data.get("gstin", "27AAPFU0939F1ZV"),
            "email":               data.get("email", "buyer@demo.com"),
            "country":             data.get("country", "India")
        },
        "rfq": {
            "product":              data.get("product", "Industrial Valves"),
            "sku":                  "PROD-001",
            "quantity":             int(data.get("quantity", 500)),
            "target_price_per_unit": int(data.get("target_price", 4200)),
            "currency":             "INR",
            "delivery_days":        int(data.get("delivery_days", 30)),
            "payment_terms":        data.get("payment_terms", "net_60")
        }
    }

    seller_policy = {
        "floor_price_per_unit":    int(data.get("floor_price", 4000)),
        "list_price_per_unit":     int(data.get("list_price", 4800)),
        "max_discount_pct":        int(data.get("max_discount", 10)),
        "min_delivery_days":       int(data.get("min_delivery", 21)),
        "accepted_payment_terms":  ["net_30", "net_45", "net_60"],
        "max_negotiation_rounds":  3
    }

    try:
        result = asyncio.run(orchestrator.run_transaction(rfq, seller_policy))
        result["transaction_id"] = txn_id
        result["timestamp"] = datetime.utcnow().isoformat()
        transaction_log.append(result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/transactions")
def get_transactions():
    return jsonify(transaction_log[-10:])


@app.route("/api/stats")
def get_stats():
    total = len(transaction_log)
    success = sum(1 for t in transaction_log if t.get("status") == "success")
    blocked = sum(1 for t in transaction_log if t.get("status") == "blocked")
    escalated = sum(1 for t in transaction_log if t.get("status") == "escalated")
    total_value = sum(
        t.get("deal", {}).get("total_value", 0)
        for t in transaction_log if t.get("deal")
    )
    return jsonify({
        "total": total,
        "success": success,
        "blocked": blocked,
        "escalated": escalated,
        "total_value": total_value
    })


if __name__ == "__main__":
    print("\n🚀 B2B Trust Engine starting...")
    print("   Open http://localhost:5000 in your browser\n")
    app.run(debug=True, port=5000)