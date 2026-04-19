"""
Orchestrator Agent
==================
Routes the transaction through all stages and manages shared state.
"""

import json
from datetime import datetime
from agents.verification_agent import VerificationAgent
from agents.negotiation_agent import NegotiationAgent
from agents.contract_agent import ContractAgent
from agents.monitor_agent import MonitorAgent
from agents.enforcement_agent import EnforcementAgent
from utils.context_store import ContextStore
from utils.logger import setup_logger

logger = setup_logger("orchestrator")


class Orchestrator:
    def __init__(self):
        self.store = ContextStore()
        self.verification = VerificationAgent()
        self.negotiation = NegotiationAgent()
        self.contract = ContractAgent()
        self.monitor = MonitorAgent()
        self.enforcement = EnforcementAgent()

    # ──────────────────────────────────────────────────────────────
    async def run_transaction(self, rfq: dict, seller_policy: dict) -> dict:
        txn_id = rfq["transaction_id"]
        logger.info(f"[{txn_id}] Starting transaction")

        # Initialise shared context store
        self.store.init(txn_id, {
            "transaction_id": txn_id,
            "stage": "verification",
            "rfq": rfq,
            "seller_policy": seller_policy,
            "audit_log": [],
            "created_at": datetime.utcnow().isoformat()
        })

        stages = [
            ("verification",  self._run_verification),
            ("negotiation",   self._run_negotiation),
            ("contract",      self._run_contract),
            ("monitoring",    self._run_monitoring),
        ]

        for stage_name, handler in stages:
            self._log_audit(txn_id, f"Starting stage: {stage_name}")
            result = await handler(txn_id)

            if result.get("status") == "blocked":
                self._log_audit(txn_id, f"BLOCKED at {stage_name}: {result.get('reason')}")
                return self._final_result(txn_id, "blocked", stage_name, result)

            if result.get("status") == "escalate_human":
                self._log_audit(txn_id, f"ESCALATED at {stage_name}: {result.get('reason')}")
                return self._final_result(txn_id, "escalated", stage_name, result)

            self.store.update(txn_id, {"stage": stage_name + "_complete"})
            self._log_audit(txn_id, f"Completed stage: {stage_name}")

        return self._final_result(txn_id, "success", "closed")

    # ──────────────────────────────────────────────────────────────
    async def _run_verification(self, txn_id: str) -> dict:
        ctx = self.store.get(txn_id)
        result = await self.verification.run(ctx["rfq"]["buyer"])
        self.store.update(txn_id, {"verification": result})
        if result["trust_score"] < 60:
            return {"status": "blocked", "reason": f"Trust score too low: {result['trust_score']}"}
        return {"status": "ok"}

    async def _run_negotiation(self, txn_id: str) -> dict:
        ctx = self.store.get(txn_id)
        result = await self.negotiation.run(ctx["rfq"], ctx["seller_policy"])
        self.store.update(txn_id, {"deal": result.get("deal"), "negotiation": result})
        if result["status"] == "escalate_human":
            return {"status": "escalate_human", "reason": "Negotiation deadlock after max rounds"}
        return {"status": "ok"}

    async def _run_contract(self, txn_id: str) -> dict:
        ctx = self.store.get(txn_id)
        result = await self.contract.run(ctx["deal"], ctx["rfq"])
        self.store.update(txn_id, {"contract": result})
        return {"status": "ok"}

    async def _run_monitoring(self, txn_id: str) -> dict:
        ctx = self.store.get(txn_id)
        result = await self.monitor.run(ctx)
        self.store.update(txn_id, {"monitoring": result})
        if result.get("breach_detected"):
            enforcement_result = await self.enforcement.run(ctx, result)
            self.store.update(txn_id, {"enforcement": enforcement_result})
        return {"status": "ok"}

    # ──────────────────────────────────────────────────────────────
    def _log_audit(self, txn_id: str, message: str):
        ctx = self.store.get(txn_id)
        log = ctx.get("audit_log", [])
        log.append({"ts": datetime.utcnow().isoformat(), "msg": message})
        self.store.update(txn_id, {"audit_log": log})
        logger.info(f"[{txn_id}] {message}")

    def _final_result(self, txn_id: str, status: str, stage: str, extra: dict = None) -> dict:
        ctx = self.store.get(txn_id)
        return {
            "status": status,
            "transaction_id": txn_id,
            "final_stage": stage,
            "deal": ctx.get("deal"),
            "negotiation": ctx.get("negotiation"),
            "contract": ctx.get("contract"),
            "verification": ctx.get("verification"),
            "monitoring": ctx.get("monitoring"),
            "enforcement": ctx.get("enforcement"),
            "audit_log": ctx.get("audit_log", []),
            **(extra or {})
        }
