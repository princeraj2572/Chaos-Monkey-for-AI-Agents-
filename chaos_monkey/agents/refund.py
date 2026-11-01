"""Refund agent: decide whether an order is refundable from the order and the refund policy."""
import json

from ..task import Task, jparse

ORDER = {"order_id": "ORD-7", "total": 45, "days_since_purchase": 12}
POLICY = {"refund_window_days": 30}


def get_order(order_id):
    return json.dumps(ORDER if order_id == ORDER["order_id"] else {"error": "unknown order"})


def get_policy():
    return json.dumps(POLICY)


def get_case(order_id):
    """Order and policy in one record; an independent source for cross-checks."""
    return json.dumps({**ORDER, **POLICY} if order_id == ORDER["order_id"] else {"error": "unknown order"})


def _answer(res):
    o, p = jparse(res[0]), jparse(res[1])
    total, days, window = o.get("total", 0), o.get("days_since_purchase", 0), p.get("refund_window_days", 0)
    if days <= window:
        return f"Refund approved for ORD-7: ${total}, {days} days since purchase, within the {window}-day window."
    return f"Refund denied for ORD-7: {days} days since purchase is past the {window}-day window."


def _consistent(res, audit):
    o, p, a = jparse(res[0]), jparse(res[1]), jparse(audit)
    return a.get("total") is not None and (
        o.get("total"), o.get("days_since_purchase"), p.get("refund_window_days")) == (
        a["total"], a.get("days_since_purchase"), a.get("refund_window_days"))


TASK = Task(
    name="refund",
    prompt=("Is order ORD-7 eligible for a refund? Use the tools, then answer in one sentence with the "
            "order total, the days since purchase and the refund window."),
    tools={"get_order": get_order, "get_policy": get_policy, "get_case": get_case},
    tool_docs=('get_order(order_id): JSON {"order_id", "total", "days_since_purchase"}\n'
               'get_policy(): JSON {"refund_window_days"}\n'
               "get_case(order_id): JSON with the order fields and refund_window_days (full record)"),
    plan=[("get_order", lambda r: {"order_id": "ORD-7"}), ("get_policy", lambda r: {})],
    answer=_answer,
    facts=("approved", "45", "12", "30"),
    audit=("get_case", {"order_id": "ORD-7"}),
    consistent=_consistent,
)
