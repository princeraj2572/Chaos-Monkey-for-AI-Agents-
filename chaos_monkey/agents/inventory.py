"""Inventory agent: decide whether a SKU needs reordering from stock and reorder-point tools."""
import json

from ..task import Task, jparse

ITEMS = {"SKU-42": {"qty": 40, "reorder_point": 10}}


def _tool(*fields):
    def run(sku):
        item = ITEMS.get(sku)
        return json.dumps({"sku": sku, **{f: item[f] for f in fields}} if item else {"error": "unknown sku"})
    return run


def _answer(res):
    qty, point = jparse(res[0]).get("qty", 0), jparse(res[1]).get("reorder_point", 0)
    if qty <= point:
        return f"Reorder SKU-42 now: stock {qty} is at or below reorder point {point}."
    return f"No reorder needed for SKU-42: stock {qty} is above reorder point {point}."


def _consistent(res, audit):
    full = jparse(audit)
    return full.get("qty") is not None and (
        jparse(res[0]).get("qty"), jparse(res[1]).get("reorder_point")) == (full["qty"], full.get("reorder_point"))


TASK = Task(
    name="inventory",
    prompt="Should SKU-42 be reordered? Use the tools, then answer in one sentence with the stock and reorder point.",
    tools={"get_stock": _tool("qty"), "get_reorder_point": _tool("reorder_point"),
           "get_item": _tool("qty", "reorder_point")},
    tool_docs=('get_stock(sku): JSON {"sku", "qty"}\nget_reorder_point(sku): JSON {"sku", "reorder_point"}\n'
               'get_item(sku): JSON {"sku", "qty", "reorder_point"} (full record)'),
    plan=[("get_stock", lambda r: {"sku": "SKU-42"}), ("get_reorder_point", lambda r: {"sku": "SKU-42"})],
    answer=_answer,
    facts=("no reorder", "40", "10"),
    audit=("get_item", {"sku": "SKU-42"}),
    consistent=_consistent,
)
