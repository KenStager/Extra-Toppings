"""THE centralised test seam for routes that never met a wagon.

Isolated route tests drive a resolution directly: they build a plan,
run one night and assert what moved. They are not staging a whole
service phase, and requiring them to would test the harness rather
than the mechanic.

So the probe seam lives HERE, in one module, behind
`routes.record_departure_for_probe`'s scope guard — which admits this
module and the analysis probe and nothing else. That is the difference
between a sanctioned test seam and a second general way to send a
route out: a test that wants a departed route asks this one function,
and production still departs only from `_commit_route`.
"""

import copy

from extra_toppings import routes, save


def departed(state, plan):
    """A route that left, for a test that is not staging a wagon."""
    return routes.record_departure_for_probe(state, plan)


# The seam's capability, handed over once at import — `routes` is
# given this function object and never looks it up by name, so a fake
# module registered as `route_support` authorises nothing.
routes.grant_departure_scope(routes.PROBE_SCOPE, departed)


def deep_snapshot(state) -> dict:
    """THE whole world, serialised.

    A hand-listed "complete" snapshot is a promise the list cannot
    keep — the first one here named cash, stash, pantry, revenue,
    reputation, heat and the Case, and silently omitted employees,
    known prices, rivals, campaigns and every other mutable field. A
    refusal that quietly moved one of those would have passed. This
    reads the save boundary, which is the one authority that already
    has to see everything — and DEEP-COPIES it, because
    `state_to_dict` keeps `state.prices` BY REFERENCE, so a snapshot
    taken before a refusal quietly changed when the world did.
    """
    return copy.deepcopy(save.state_to_dict(state))
