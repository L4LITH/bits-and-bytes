from datetime import date
from itertools import combinations

NSAIDS = ["ibuprofen", "naproxen", "diclofenac", "aspirin"]
ACE_INHIBITORS = ["enalapril", "lisinopril", "ramipril"]

# Small hand-written list of well-known interactions (demo scope, not a full database)
INTERACTIONS = {
    frozenset(("sildenafil", "isosorbide")): "Can cause a dangerous drop in blood pressure.",
    frozenset(("tramadol", "sertraline")): "Risk of serotonin syndrome.",
    frozenset(("clopidogrel", "omeprazole")): "Omeprazole may reduce the effect of clopidogrel.",
    frozenset(("simvastatin", "amlodipine")): "Raises simvastatin levels, increasing the risk of muscle damage.",
}
for n in NSAIDS:
    INTERACTIONS[frozenset(("warfarin", n))] = "Increased risk of serious bleeding."
for n in NSAIDS:
    for a in ACE_INHIBITORS:
        INTERACTIONS[frozenset((n, a))] = "Can weaken blood pressure control and strain the kidneys."


def _key(m):
    """Compare by active ingredient; fall back to the brand name if no generic."""
    return (m.get("generic") or m.get("name") or "").strip().lower()


def duplicate_medicines(meds):
    groups = {}
    for m in meds:
        if _key(m):
            groups.setdefault(_key(m), []).append(m)
    alerts = []
    for k, items in groups.items():
        doctors = {i["doctor"] for i in items if i["doctor"]}
        if len(doctors) > 1:          # same drug from different doctors
            seen = "; ".join(f"{i['doctor'] or '?'} ({i['name']}, {i['date'] or 'no date'})"
                             for i in items)
            alerts.append({"level": "warning",
                           "title": f"Possible duplicate medicine: {k}",
                           "detail": f"Prescribed by more than one doctor: {seen}."})
    return alerts


def interactions(meds):
    present = {}
    for m in meds:
        if _key(m):
            present.setdefault(_key(m), m)
    alerts = []
    for a, b in combinations(present, 2):
        note = INTERACTIONS.get(frozenset((a, b)))
        if note:
            ma, mb = present[a], present[b]
            alerts.append({"level": "high",
                           "title": f"Possible interaction: {a} + {b}",
                           "detail": f"{note} {a} from {ma['doctor'] or '?'}, {b} from {mb['doctor'] or '?'}."})
    return alerts


def repeated_tests(labs, days=30):
    groups = {}
    for l in labs:
        if l["test_name"] and l["date"]:
            groups.setdefault(l["test_name"].strip().lower(), []).append(l)
    alerts = []
    for name, items in groups.items():
        items.sort(key=lambda x: x["date"])
        for prev, cur in zip(items, items[1:]):
            try:
                gap = (date.fromisoformat(cur["date"]) - date.fromisoformat(prev["date"])).days
            except ValueError:
                continue
            if 0 < gap <= days:
                alerts.append({"level": "warning",
                               "title": f"Repeated test: {prev['test_name']}",
                               "detail": f"Done on {prev['date']} ({prev['doctor'] or '?'}) and again on "
                                         f"{cur['date']} ({cur['doctor'] or '?'}), {gap} days apart."})
    return alerts


def run_alerts(meds, labs):
    return interactions(meds) + duplicate_medicines(meds) + repeated_tests(labs)