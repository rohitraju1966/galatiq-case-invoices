import json


def parse_decision(response: str, default: str = "rejected") -> tuple[str, str]:
    try:
        data = json.loads(response)
        return data["decision"], data["reasoning"]
    except (json.JSONDecodeError, KeyError):
        decision = "approved" if "approve" in response.lower() else default
        return decision, response
