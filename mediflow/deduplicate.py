"""Classify each row once and detect conflicting source versions."""
from collections import defaultdict
from .evidence import canonical


def classify(valid, existing):
    groups = defaultdict(list)
    counts = dict(duplicate=0, stale=0, superseded=0, accepted=0, invalid=0)
    rejects, winners = [], {}
    for entry in valid:
        entity, line, sha, row = entry
        groups[(entity, row["id"])].append(entry)
    for key, entries in groups.items():
        current = existing[key[0]].get(key[1])
        by_version = defaultdict(list)
        for item in entries:
            by_version[item[3]["source_version"]].append(item)
        eligible = []
        for version, items in by_version.items():
            payloads = {canonical(i[3]) for i in items}
            if current and version == current["source_version"]:
                payloads.add(canonical(current))
            if len(payloads) > 1:
                counts["invalid"] += len(items)
                rejects.extend({"entity": i[0], "line": i[1], "source_sha256": i[2], "reason": "VERSION_CONFLICT", "record": i[3]} for i in items)
            elif current and version <= current["source_version"]:
                counts["duplicate" if version == current["source_version"] else "stale"] += len(items)
            else:
                counts["duplicate"] += len(items) - 1
                eligible.append(items[0])
        if eligible:
            winner = max(eligible, key=lambda x: x[3]["source_version"])
            counts["superseded"] += len(eligible) - 1
            counts["accepted"] += 1
            winners[key] = winner
    return winners, counts, rejects
