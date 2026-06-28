import json
import logging

from langgraph.prebuilt import create_react_agent

from agents.state import InvoiceState
from agents.tools.db import InvoiceDB
from agents.tools.auditor import make_auditor_tools
from agents.prompts.auditor import AUDITOR_CRITIQUE_PROMPT
from llm import llm

logger = logging.getLogger(__name__)
db = InvoiceDB()


def auditor_review(state: InvoiceState) -> dict:
    auditor_tools = make_auditor_tools(state["trn_id"])

    prompt = AUDITOR_CRITIQUE_PROMPT.format(
        invoice_data=json.dumps(state["invoice_data"], indent=2),
        validation_flags="\n".join(state["validation_flags"]) if state["validation_flags"] else "No flags",
        vp_reasoning=state["review_note"],
    )

    agent = create_react_agent(llm, auditor_tools, prompt=prompt)

    critique = ""
    for step in agent.stream({"messages": [("human", "Review the VP's decision.")]}, config={"recursion_limit": 10}):
        for node, output in step.items():
            if node == "tools":
                for msg in output["messages"]:
                    logger.info(f"Auditor Tool [{msg.name}]: {msg.content}")
            elif node == "agent":
                content = output["messages"][-1].content
                if content:
                    logger.info(f"Auditor critique: {content}")
                    critique = content

    db.log_audit(state["trn_id"], "auditor_reviewed", critique, "auditor_agent")
    logger.info(f"Auditor critique complete, sending back to VP")

    return {
        "status": "vp_review_required",
        "critique": critique,
        "reviewed_by": "auditor_agent",
        "review_count": state.get("review_count", 0) + 1,
    }
