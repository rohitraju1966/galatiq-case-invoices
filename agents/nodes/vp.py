import json
import logging

from langgraph.prebuilt import create_react_agent

from agents.state import InvoiceState
from agents.tools.db import InvoiceDB
from agents.prompts.vp import VP_PROMPT, VP_CRITIQUE_SECTION
from config import APPROVAL_THRESHOLD
from llm import llm
from agents.tools.vp import get_merchant_details, get_item_details, get_invoice_history
from agents.tools.utils import parse_decision

logger = logging.getLogger(__name__)

vp_tools = [get_merchant_details, get_item_details, get_invoice_history]

def run_vp(state: InvoiceState, critique_section: str = "") -> str:
    prompt = VP_PROMPT.format(
        critique_section=critique_section,
        invoice_data=json.dumps(state["invoice_data"], indent=2),
        validation_flags="\n".join(state["validation_flags"]) if state["validation_flags"] else "No flags — all checks passed",
    )
    agent = create_react_agent(llm, vp_tools, prompt=prompt)
    
    final_response = ""
    for step in agent.stream({"messages": [("human", "Review this invoice.")]}, config={"recursion_limit": 10}):
        for node, output in step.items():
            if node == "tools":
                for msg in output["messages"]:
                    logger.info(f"Tool [{msg.name}]: {msg.content}")
            elif node == "agent":
                content = output["messages"][-1].content
                if content:
                    logger.info(f"VP reasoning: {content}")
                    final_response = content
    
    return final_response

db = InvoiceDB()
def vp_review(state: InvoiceState) -> dict:
    critique_section = ""
    if state.get("status") == "vp_review_required":
        critique_section = VP_CRITIQUE_SECTION.format(
            threshold=f"{APPROVAL_THRESHOLD:,.0f}",
            initial_reasoning=state.get("review_note", ""),
            critique=state.get("critique", ""),
        )

    raw_response = run_vp(state, critique_section=critique_section)
    decision, reasoning = parse_decision(raw_response)
    logger.info(f"VP decision: {decision}, reasoning: {reasoning}")

    db.log_audit(state["trn_id"], decision, reasoning, "vp_agent")

    return {
        "status": decision,
        "review_note": reasoning,
        "reviewed_by": "vp_agent",
    }