"""Example agents, keyed by CLI name."""
from . import inventory, refund, research

AGENTS = {"research": research.TASK, "inventory": inventory.TASK, "refund": refund.TASK}
