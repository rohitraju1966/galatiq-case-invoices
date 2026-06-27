import json
import logging

from langgraph.prebuilt import create_react_agent

from agents.state import InvoiceState
from agents.tools.db import InvoiceDB
from agents.tools.management import make_management_tools
from agents.prompts.management import MANAGEMENT_CRITIQUE_PROMPT
from llm import llm

logger = logging.getLogger(__name__)
db = InvoiceDB()


def management_review(state: InvoiceState) -> dict:
    mgmt_tools = make_management_tools(state["trn_id"])

    prompt = MANAGEMENT_CRITIQUE_PROMPT.format(
        invoice_data=json.dumps(state["invoice_data"], indent=2),
        validation_flags="\n".join(state["validation_flags"]) if state["validation_flags"] else "No flags",
        vp_reasoning=state["review_note"],
    )

    agent = create_react_agent(llm, mgmt_tools, prompt=prompt)

    critique = ""
    for step in agent.stream({"messages": [("human", "Review the VP's decision.")]}, config={"recursion_limit": 10}):
        for node, output in step.items():
            if node == "tools":
                for msg in output["messages"]:
                    logger.info(f"Mgmt Tool [{msg.name}]: {msg.content}")
            elif node == "agent":
                content = output["messages"][-1].content
                if content:
                    logger.info(f"Management critique: {content}")
                    critique = content

    db.log_audit(state["trn_id"], "management_reviewed", critique, "management_agent")
    logger.info(f"Management critique complete, sending back to VP")

    return {
        "status": "vp_review_required",
        "critique": critique,
        "reviewed_by": "management_agent",
        "review_count": state.get("review_count", 0) + 1,
    }
