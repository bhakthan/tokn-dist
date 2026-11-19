"""A deliberately misleading eval: it never runs TOKN, so the candidate prompt never reaches a model.

It scores better whenever the candidate overlay is present. `tokn self-harness --require-witness`
must reject it, because the witness file stays empty. TOKN_EXAMPLE_TOKEN_FACTOR multiplies the
candidate's token count, which exercises the token-budget gate.
"""

import json
import os

candidate = bool(os.environ.get("TOKN_PROMPTS_OVERLAY_DIR"))
factor = float(os.environ.get("TOKN_EXAMPLE_TOKEN_FACTOR", "1"))
cases = 4
solved = 4 if candidate else 2
tokens = cases * 1000 * (factor if candidate else 1)
print(json.dumps({
    "dimensions": {"accuracy": solved / cases, "tokens_total": tokens, "cases": cases, "solved": solved},
    "gates": {"no_false_verified": True},
}))
