"""
Filename-based agreement search over the agreements/ folder.
Parses CC -> UC articulation data from ASSIST.org JSON files.
"""
import json, os
from difflib import SequenceMatcher

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AGREEMENTS_DIR = os.path.join(BASE_DIR, "agreements")

UC_ALIASES = {
    "berkeley": "Berkeley", "ucb": "Berkeley", "cal": "Berkeley",
    "ucla": "Los_Angeles", "los angeles": "Los_Angeles",
    "ucsd": "San_Diego", "san diego": "San_Diego",
    "ucsb": "Santa_Barbara", "santa barbara": "Santa_Barbara",
    "ucd": "Davis", "uc davis": "Davis", "davis": "Davis",
    "uci": "Irvine", "irvine": "Irvine",
    "ucr": "Riverside", "riverside": "Riverside",
    "ucsc": "Santa_Cruz", "santa cruz": "Santa_Cruz",
    "ucm": "Merced", "merced": "Merced",
}

_INDEX = []


def _build_index():
    global _INDEX
    if _INDEX or not os.path.isdir(AGREEMENTS_DIR):
        return
    for fname in os.listdir(AGREEMENTS_DIR):
        if not fname.endswith(".json"):
            continue
        parts = fname[:-5].split("__")
        if len(parts) >= 3:
            cc = parts[0].replace("_", " ")
            uc = parts[1].replace("_", " ")
            major = "__".join(parts[2:]).replace("_", " ")
            _INDEX.append({"cc": cc, "uc": uc, "major": major, "fname": fname})


_build_index()


def _sim(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def detect_uc(query):
    q = query.lower()
    for alias, key in UC_ALIASES.items():
        if alias in q:
            return key.replace("_", " ")
    return None


def detect_cc(query):
    q = query.lower()
    best_score, best_cc = 0, None
    seen = set()
    for entry in _INDEX:
        cc = entry["cc"]
        if cc in seen:
            continue
        seen.add(cc)
        skip_words = {"college", "community", "district", "valley", "coast", "center"}
        words = [w for w in cc.lower().split() if len(w) >= 3 and w not in skip_words]
        if any(w in q for w in words):
            score = 0.7
        else:
            score = _sim(q, cc.lower())
        if score > best_score:
            best_score = score
            best_cc = cc
    return best_cc if best_score >= 0.5 else None


def search_agreements(query, max_results=3):
    uc = detect_uc(query)
    cc = detect_cc(query)
    if not uc and not cc:
        return []

    q = query.lower()
    scored = []
    for entry in _INDEX:
        score = 0
        if uc and uc.lower() in entry["uc"].lower():
            score += 3
        if cc and (entry["cc"].lower() == cc.lower() or _sim(entry["cc"].lower(), cc.lower()) > 0.85):
            score += 3
        major_words = [w for w in entry["major"].lower().split() if len(w) > 3]
        score += sum(1 for w in major_words if w in q)
        if score >= 3:
            scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for _, entry in scored[:max_results]:
        path = os.path.join(AGREEMENTS_DIR, entry["fname"])
        parsed = _parse_agreement(path)
        if parsed:
            results.append(parsed)
    return results


def _get_inst_name(inst_raw):
    try:
        inst = json.loads(inst_raw) if isinstance(inst_raw, str) else inst_raw
        names = inst.get("names", [])
        if names and isinstance(names, list):
            return names[0].get("name", "Unknown")
    except Exception:
        pass
    return "Unknown"


def _parse_agreement(filepath):
    try:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        result = data.get("result", {})
        major = result.get("name", "Unknown Major")
        recv_name = _get_inst_name(result.get("receivingInstitution", {}))
        send_name = _get_inst_name(result.get("sendingInstitution", {}))

        arts_raw = result.get("articulations", "[]")
        articulations = json.loads(arts_raw) if isinstance(arts_raw, str) else (arts_raw or [])

        lines = [f"=== {major} | {send_name} -> {recv_name} ==="]
        count = 0
        for art in articulations:
            if not isinstance(art, dict):
                continue
            inner = art.get("articulation", {})
            uc_course = inner.get("course", {})
            if not uc_course:
                continue
            uc_str = (
                f"{uc_course.get('prefix','')} {uc_course.get('courseNumber','')}"
                f" - {uc_course.get('courseTitle','')} ({uc_course.get('maxUnits','?')} units)"
            )
            sa = inner.get("sendingArticulation", {})
            reason = sa.get("noArticulationReason", "")
            items = sa.get("items", [])

            if reason:
                lines.append(f"  UC: {uc_str}")
                lines.append(f"    -> {reason}")
            elif items:
                cc_parts = []
                for group in items:
                    if not isinstance(group, dict):
                        continue
                    conj = group.get("courseConjunction", "Or")
                    g_items = group.get("items", [])
                    strs = [
                        f"{c.get('prefix','')} {c.get('courseNumber','')} - {c.get('courseTitle','')} ({c.get('maxUnits','?')} units)"
                        for c in g_items if isinstance(c, dict)
                    ]
                    if strs:
                        cc_parts.append(f" {conj} ".join(strs))
                lines.append(f"  UC: {uc_str}")
                for cp in cc_parts:
                    lines.append(f"    CC: {cp}")
            else:
                lines.append(f"  UC: {uc_str}")
                lines.append(f"    CC: No direct equivalent at this CC")
            count += 1
            if count >= 20:
                lines.append("  ... (additional requirements exist)")
                break

        return "\n".join(lines)
    except Exception:
        return None
