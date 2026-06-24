"""
Keyword-based search over static data files.
"""
import json, os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

_cache = {}


def _load(filename):
    if filename not in _cache:
        path = os.path.join(DATA_DIR, filename)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                _cache[filename] = json.load(f)
        else:
            _cache[filename] = None
    return _cache[filename]


UC_FULL_NAMES = {
    "berkeley": "University of California, Berkeley",
    "ucb": "University of California, Berkeley",
    "cal": "University of California, Berkeley",
    "ucla": "University of California, Los Angeles",
    "los angeles": "University of California, Los Angeles",
    "ucsd": "University of California, San Diego",
    "san diego": "University of California, San Diego",
    "ucsb": "University of California, Santa Barbara",
    "santa barbara": "University of California, Santa Barbara",
    "davis": "University of California, Davis",
    "ucd": "University of California, Davis",
    "irvine": "University of California, Irvine",
    "uci": "University of California, Irvine",
    "riverside": "University of California, Riverside",
    "ucr": "University of California, Riverside",
    "santa cruz": "University of California, Santa Cruz",
    "ucsc": "University of California, Santa Cruz",
    "merced": "University of California, Merced",
    "ucm": "University of California, Merced",
}

UC_SHORT_NAMES = {
    "berkeley": "UC Berkeley", "ucb": "UC Berkeley", "cal": "UC Berkeley",
    "ucla": "UCLA", "los angeles": "UCLA",
    "ucsd": "UC San Diego", "san diego": "UC San Diego",
    "ucsb": "UC Santa Barbara", "santa barbara": "UC Santa Barbara",
    "davis": "UC Davis", "ucd": "UC Davis",
    "irvine": "UC Irvine", "uci": "UC Irvine",
    "riverside": "UC Riverside", "ucr": "UC Riverside",
    "santa cruz": "UC Santa Cruz", "ucsc": "UC Santa Cruz",
    "merced": "UC Merced", "ucm": "UC Merced",
}


def _detect_uc_full(query):
    q = query.lower()
    # Check longer aliases first to avoid substring false matches
    for alias in sorted(UC_FULL_NAMES, key=len, reverse=True):
        if alias in q:
            # Avoid "cal" matching "california", "irvine" matching "irvine" is fine
            if len(alias) <= 3:
                # Require word boundary for very short aliases
                import re
                if re.search(r'\b' + re.escape(alias) + r'\b', q):
                    return UC_FULL_NAMES[alias]
            else:
                return UC_FULL_NAMES[alias]
    return None


def _detect_uc_short(query):
    q = query.lower()
    for alias in sorted(UC_SHORT_NAMES, key=len, reverse=True):
        if alias in q:
            if len(alias) <= 3:
                import re
                if re.search(r'\b' + re.escape(alias) + r'\b', q):
                    return UC_SHORT_NAMES[alias]
            else:
                return UC_SHORT_NAMES[alias]
    return None


def search_static(query):
    q = query.lower()
    parts = []

    # --- TAG ---
    if any(w in q for w in ["tag", "transfer admission guarantee", "guaranteed admission", "tap"]):
        data = _load("tag_requirements.json")
        if data:
            uc_full = _detect_uc_full(query)
            campuses = data.get("campuses", [])
            campus_map = {c["name"]: c for c in campuses if isinstance(c, dict) and "name" in c}
            matched = campus_map.get(uc_full) if uc_full else None

            if matched:
                gpa = matched.get("minGPA", {})
                gpa_str = (", ".join(f"{k}: {v}" for k, v in gpa.items())
                           if isinstance(gpa, dict) else str(gpa))
                excluded = matched.get("excludedMajors", [])
                shared = data.get("sharedCriteria", {})
                notes = matched.get("notes", "")
                tag_lines = [
                    f"TAG for {uc_full}:",
                    f"  What TAG means: GUARANTEED ADMISSION to this UC campus if all requirements are met (not just a review -- that is TAP).",
                    f"  Min GPA: {gpa_str}",
                    f"  Excluded majors: {', '.join(excluded[:6]) if excluded else 'None listed'}",
                    f"  Filing period: {matched.get('filingPeriod', 'September 1-30')}",
                ]
                if shared:
                    tag_lines.append(f"  Shared criteria: {json.dumps(shared)[:200]}")
                if notes:
                    tag_lines.append(f"  Notes: {notes[:200]}")
                parts.append("\n".join(tag_lines))
            else:
                names = [c.get("shortName", c.get("name", "")) for c in campuses]
                parts.append(
                    f"TAG (Transfer Admission Guarantee) GUARANTEES ADMISSION to the UC campus if requirements are met -- not just a review. "
                    f"IMPORTANT: TAP (Transfer Alliance Program) is different -- TAP only guarantees a thorough review, NOT admission. Do not confuse TAG with TAP. "
                    f"TAG offered by 6 UCs: {', '.join(names)}. "
                    f"UCLA, UC Berkeley, and UCSD do NOT offer TAG. "
                    f"Filing period: September 1-30 (the year before you transfer). "
                    f"GPA requirements: Merced 2.8, Riverside 2.4, Davis 3.2, "
                    f"Santa Cruz 3.0, Irvine 3.4, Santa Barbara 3.4."
                )

    # --- Cost of attendance ---
    if any(w in q for w in ["cost", "tuition", "fees", "afford", "financial aid", "expensive", "price", "money", "pay", "how much"]):
        data = _load("cost_of_attendance.json")
        if data:
            uc_full = _detect_uc_full(query)
            campuses = data.get("campuses", {})
            c = campuses.get(uc_full) if uc_full else None
            if c:
                parts.append(
                    f"Cost of Attendance at {c.get('shortName', uc_full)} (2024-25, CA resident, on-campus):\n"
                    f"  Tuition: ${c['tuition']:,}\n"
                    f"  Fees: ${c.get('fees',0):,}\n"
                    f"  Room & Board: ${c.get('roomAndBoard',0):,}\n"
                    f"  Total: ${c['total']:,}/year\n"
                    f"  Non-resident total: ${c.get('totalNonResident',0):,}/year\n"
                    f"  Note: {c.get('notes','')}"
                )
            else:
                lines = ["UC Cost of Attendance 2024-25 (CA Resident, on-campus):"]
                for name, c in campuses.items():
                    short = c.get("shortName", name.replace("University of California, ", "UC "))
                    lines.append(f"  {short}: ${c['total']:,}/year")
                fa = data.get("financialAidContext", {})
                if fa:
                    lines.append(f"\nBlue & Gold: {fa.get('ucBlueAndGold','')[:150]}")
                parts.append("\n".join(lines))

    # --- Admit rates ---
    if any(w in q for w in ["admit rate", "acceptance rate", "chances", "how hard", "competitive", "selectiv", "get in"]):
        data = _load("transfer_admit_rates.json")
        if data:
            uc_short = _detect_uc_short(query)
            campuses = data.get("campuses", [])
            matched = None
            if uc_short:
                for c in campuses:
                    if uc_short.lower() in c.get("campus", "").lower():
                        matched = c
                        break
            if matched:
                raw = matched.get("rawText", "")
                # Extract admit rate from rawText
                import re
                rate_match = re.search(r'(\d+(?:\.\d+)?)\s*%', raw)
                rate = rate_match.group(0) if rate_match else "see rawText"
                parts.append(
                    f"Transfer admit stats at {matched['campus']}:\n"
                    f"  Applicants: {matched.get('applicants','N/A')}\n"
                    f"  Admits: {matched.get('admits','N/A')}\n"
                    f"  Admit rate: {rate}"
                )
            else:
                lines = ["UC Transfer Admit Rates (Fall 2025):"]
                # Hardcoded known rates since rawText parsing is complex
                known = {
                    "UC Berkeley": "~24%", "UCLA": "~23%", "UC San Diego": "~53%",
                    "UC Santa Barbara": "~59%", "UC Davis": "~57%", "UC Irvine": "~38%",
                    "UC Riverside": "~68%", "UC Santa Cruz": "~69%", "UC Merced": "~72%"
                }
                for name, rate in known.items():
                    lines.append(f"  {name}: {rate}")
                parts.append("\n".join(lines))

    # --- GPA context ---
    if any(w in q for w in ["gpa", "grade point", "grades needed", "what gpa", "minimum gpa"]):
        data = _load("transfer_gpa_context.json")
        if data:
            uc_short = _detect_uc_short(query)
            campuses = data.get("campuses", {})
            c = campuses.get(uc_short) if uc_short else None
            if c:
                parts.append(
                    f"Transfer GPA context at {uc_short}:\n"
                    f"  Typical 25th percentile: {c.get('typical25th','N/A')}\n"
                    f"  Typical 75th percentile: {c.get('typical75th','N/A')}\n"
                    f"  Note: {c.get('note','')}"
                )
            else:
                lines = ["UC Transfer GPA Ranges (25th - 75th percentile):"]
                for name, c in campuses.items():
                    lines.append(f"  {name}: {c.get('typical25th','?')} - {c.get('typical75th','?')}")
                lines.append("\nUC systemwide minimum transfer GPA: 2.4 (competitive campuses need 3.5+)")
                parts.append("\n".join(lines))

    # --- IGETC ---
    if any(w in q for w in ["igetc", "general ed", "general education", "area 1", "area 2", "area 3", "area 4", "area 5", "area 6"]):
        data = _load("igetc_map.json")
        if data:
            from search_agreements import detect_cc
            cc = detect_cc(query)
            area_map = {"1a": "1A", "1b": "1B", "2a": "2A", "3a": "3A", "3b": "3B",
                        "4": "4", "5a": "5A", "5b": "5B", "5c": "5C", "6a": "6A"}
            area_hint = None
            for code in area_map:
                if code in q:
                    area_hint = area_map[code]
                    break

            schools = data.get("schools", {})
            if cc and schools:
                school_key = next((k for k in schools if cc.lower() in k.lower() or k.lower() in cc.lower()), None)
                if school_key:
                    school_data = schools[school_key]
                    areas = school_data.get("areas", {}) if isinstance(school_data, dict) else {}
                    if area_hint and area_hint in areas:
                        courses = areas[area_hint]
                        lines = [f"IGETC Area {area_hint} courses at {school_key}:"]
                        for c in (courses[:10] if isinstance(courses, list) else []):
                            if isinstance(c, dict):
                                lines.append(f"  {c.get('prefix','')} {c.get('courseNumber','')} - {c.get('courseTitle','')} ({c.get('maxUnits','?')} units)")
                        parts.append("\n".join(lines))
                    else:
                        covered = sorted(areas.keys()) if isinstance(areas, dict) else []
                        parts.append(f"IGETC areas covered at {school_key}: {', '.join(covered)}")
            else:
                parts.append(
                    "IGETC areas: 1A (English Comp), 1B (Critical Thinking), 2A (Math), "
                    "3A (Arts), 3B (Humanities), 4 (Social Science), "
                    "5A (Physical Science), 5B (Bio Science), 5C (Lab), 6A (Foreign Language). "
                    "Completing IGETC satisfies lower-division GE requirements at all UC campuses."
                )

    # --- Essay evaluation (student submits their own essay for review) ---
    essay_eval_keywords = ["review my essay", "check my essay", "grade my essay", "evaluate my essay",
                           "feedback on my essay", "is my essay good", "rate my essay", "my piq",
                           "my personal insight", "can you review", "critique my", "look at my essay",
                           "here is my essay", "here's my essay", "my draft", "what do you think of my"]
    is_essay_submission = any(kw in q for kw in essay_eval_keywords)

    if is_essay_submission:
        examples = _load("piq_examples.json")
        admitted = _load("piq_admitted_essays.json")
        if examples:
            rubric = examples.get("essay_evaluation_rubric", {})
            real = examples.get("real_admitted_essays", {})
            berk = real.get("berkeley_transfer_admit", {})
            berk_essays = berk.get("essays", {})
            lines = [
                "ESSAY EVALUATION CONTEXT — use this rubric and the real examples below to evaluate the student's essay.",
                "",
                "RUBRIC DIMENSIONS:",
            ]
            dims = rubric.get("dimensions", {})
            for dim_name, dim_data in dims.items():
                label = dim_name.replace("_", " ").title()
                what = dim_data.get("what_to_look_for", "")
                lines.append(f"  {label} [{dim_data.get('weight','?')} weight]: {what[:180]}")
            scores = rubric.get("scoring", {})
            if scores:
                lines.append("\nOVERALL RATINGS:")
                for rating, desc in scores.items():
                    lines.append(f"  {rating.title()}: {desc}")
            if berk_essays:
                lines.append(f"\nREAL ADMITTED STUDENT ESSAYS — UC Berkeley transfer (source: {berk.get('source','public post')}):")
                for key, essay_data in berk_essays.items():
                    prompt_label = key.replace("_", " ").title()
                    lines.append(f"\n[{prompt_label}]")
                    lines.append(essay_data.get("essay", "")[:500])
                    lines.append(f"What worked: {essay_data.get('notes','')}")
            # Also pull a relevant essay from the professional guides file
            if admitted:
                prompts = admitted.get("prompts", {})
                # Try to detect which prompt the student is writing for
                prompt_key_map = {
                    "leadership": "prompt_1_leadership",
                    "creativ": "prompt_2_creativity",
                    "talent": "prompt_3_talent",
                    "educational": "prompt_4_educational_opportunity",
                    "challenge": "prompt_5_challenge",
                    "academic subject": "prompt_6_academic_subject",
                    "community": "prompt_7_community",
                    "stand out": "prompt_8_stand_out",
                    "transfer required": "transfer_required_question",
                    "major prep": "transfer_required_question",
                    "intended major": "transfer_required_question",
                }
                matched_key = None
                for kw, pk in prompt_key_map.items():
                    if kw in q:
                        matched_key = pk
                        break
                if matched_key and prompts.get(matched_key):
                    pd = prompts[matched_key]
                    pd_essays = pd.get("essays", [])
                    if pd_essays:
                        e = pd_essays[0]
                        lines.append(f"\nPROFESSIONAL GUIDE EXAMPLE — {e.get('source','')} (admitted: {e.get('admission','')}):")
                        lines.append(e.get("essay","")[:600])
                        lines.append(f"What works: {e.get('analysis','')}")
            parts.append("\n".join(lines))

    # --- PIQ / Essays ---
    if any(w in q for w in ["piq", "personal insight", "essay", "application essay", "prompt", "how to write",
                             "writing tips", "example essay", "sample essay", "piq example", "piq help",
                             "personal statement", "leadership essay", "challenge essay", "creativity essay"]):
        data = _load("piq_guidance.json")
        examples = _load("piq_examples.json")
        guidance = examples.get("question_guidance", {}) if examples else {}
        model_essays = examples.get("model_essays", {}) if examples else {}

        # Detect which prompt they are asking about
        prompt_map = {
            "leadership": "1_leadership", "lead": "1_leadership",
            "creativ": "2_creativity", "creative": "2_creativity",
            "talent": "3_talent", "skill": "3_talent",
            "educational": "4_educational", "barrier": "4_educational", "opportunity": "4_educational",
            "challenge": "5_challenge", "difficult": "5_challenge", "obstacle": "5_challenge",
            "academic subject": "6_academic_subject", "inspires": "6_academic_subject", "subject": "6_academic_subject",
            "community": "7_community", "make your school": "7_community",
            "stand out": "8_standout", "standout": "8_standout", "what makes you": "8_standout",
            "transfer required": "transfer_required", "major prep": "transfer_required",
        }
        matched_prompt = None
        for kw, pid in prompt_map.items():
            if kw in q:
                matched_prompt = pid
                break

        real_admitted = examples.get("real_admitted_essays", {}) if examples else {}
        berk_real = real_admitted.get("berkeley_transfer_admit", {})
        berk_essays = berk_real.get("essays", {})
        admitted_guide = _load("piq_admitted_essays.json") or {}
        admitted_prompts = admitted_guide.get("prompts", {})

        if matched_prompt and model_essays.get(matched_prompt):
            essay_data = model_essays[matched_prompt]
            guide_data = guidance.get(matched_prompt, {})
            lines = [
                f"PIQ Prompt — {essay_data.get('prompt', '')}",
                f"Student profile: {essay_data.get('student_profile', '')}",
                "",
                "Model essay example:",
                essay_data.get("essay", ""),
                "",
                "What makes this essay strong:",
            ]
            framework = guide_data.get("structural_framework", [])
            for step in framework[:4]:
                lines.append(f"  - {step}")
            if guide_data.get("common_mistakes"):
                lines.append("\nCommon mistakes to avoid:")
                for m in guide_data["common_mistakes"][:3]:
                    lines.append(f"  - {m}")
            # Map old prompt IDs to Berkeley real essay keys
            prompt_to_berk = {
                "3_talent": "greatest_talent",
                "5_challenge": "significant_challenge",
                "8_standout": "what_makes_you_stand_out",
                "transfer_required": "major_preparation",
            }
            berk_key = prompt_to_berk.get(matched_prompt)
            if berk_key and berk_essays.get(berk_key):
                real_e = berk_essays[berk_key]
                lines.append(f"\nREAL EXAMPLE — UC Berkeley admitted transfer student (source: {berk_real.get('source','public post')}):")
                lines.append(real_e.get("essay", "")[:500])
                lines.append(f"What worked: {real_e.get('notes','')}")
            # Also pull from professional guide admitted essays
            guide_prompt_map = {
                "1_leadership": "prompt_1_leadership",
                "2_creativity": "prompt_2_creativity",
                "3_talent": "prompt_3_talent",
                "4_educational": "prompt_4_educational_opportunity",
                "5_challenge": "prompt_5_challenge",
                "6_academic_subject": "prompt_6_academic_subject",
                "7_community": "prompt_7_community",
                "8_standout": "prompt_8_stand_out",
                "transfer_required": "transfer_required_question",
            }
            guide_key = guide_prompt_map.get(matched_prompt)
            if guide_key and admitted_prompts.get(guide_key):
                pd = admitted_prompts[guide_key]
                pd_essays = pd.get("essays", [])
                if pd_essays:
                    ge = pd_essays[0]
                    src = ge.get("source", "professional college prep guide")
                    adm = ge.get("admission", "UCLA or UC Berkeley")
                    lines.append(f"\nPROFESSIONAL GUIDE EXAMPLE — {src} (admitted: {adm}):")
                    lines.append(ge.get("essay", "")[:600])
                    lines.append(f"What works: {ge.get('analysis','')}")
            parts.append("\n".join(lines))
        else:
            if data:
                fmt = data.get("format", {})
                req = data.get("required_prompt", {})
                lines = [
                    "UC Personal Insight Questions (PIQ) for transfer applicants:",
                    f"  Required question (transfers only): {req.get('prompt','')[:180]}",
                    f"  Plus choose 3 of 8 additional prompts. Word limit: {fmt.get('word_limit_per_question',350)} words each.",
                    "",
                    "The 8 prompts cover: (1) leadership, (2) creativity, (3) talent/skill,",
                    "(4) educational opportunity or barrier, (5) most significant challenge,",
                    "(6) academic subject that inspires you, (7) community contribution,",
                    "(8) what makes you stand out.",
                ]
                if examples:
                    sel = examples.get("question_selection_guide", {})
                    principles = examples.get("transfer_essay_principles", {}).get("principles", [])
                    lines.append("\nKey writing principles for transfer students:")
                    for p in principles[:5]:
                        lines.append(f"  - {p}")
                    if sel.get("avoid"):
                        lines.append("\nQuestion selection tips:")
                        for a in sel["avoid"][:3]:
                            lines.append(f"  - {a}")
                if berk_essays:
                    lines.append(f"\nREAL UC BERKELEY TRANSFER ESSAYS (source: {berk_real.get('source','public post')}):")
                    for key, real_e in list(berk_essays.items())[:2]:
                        lines.append(f"\n[Prompt: {real_e.get('prompt', key)}]")
                        lines.append(real_e.get("essay", "")[:400] + "...")
                        lines.append(f"What worked: {real_e.get('notes','')}")
                if admitted_prompts:
                    lines.append("\nESSAYS FROM ADMITTED UCLA / UC BERKELEY STUDENTS (Winning Ivy Prep + Shemmassian guides):")
                    for pk, pd in list(admitted_prompts.items())[:3]:
                        pd_essays = pd.get("essays", [])
                        if pd_essays:
                            ge = pd_essays[0]
                            label = pk.replace("_", " ").replace("prompt ", "Prompt ").title()
                            lines.append(f"\n[{label}] — {ge.get('source','')} (admitted: {ge.get('admission','')})")
                            lines.append(ge.get("essay","")[:350] + "...")
                parts.append("\n".join(lines))

    # --- Scholarships ---
    if any(w in q for w in ["scholarship", "grant", "blue and gold", "cal grant", "free money", "financial aid",
                             "afford", "pell", "dream act", "ab 540", "undocumented", "fafsa", "cadaa",
                             "jack kent cooke", "regents", "hispanic scholarship", "daca", "cost"]):
        data = _load("scholarships.json")
        if data:
            lines = ["Transfer scholarships and financial aid:"]
            # Detect specific scholarship questions
            is_dream = any(w in q for w in ["dream act", "ab 540", "undocumented", "daca", "cadaa"])
            is_pell  = any(w in q for w in ["pell", "federal grant"])
            is_jkc   = any(w in q for w in ["jack kent", "cooke", "jkc"])
            is_cal   = any(w in q for w in ["cal grant"])

            if is_dream:
                da = data.get("dreamActAB540", {})
                if da:
                    lines = [
                        f"California Dream Act (AB 540):",
                        f"  {da.get('description','')}",
                        f"  Amount: {da.get('amount','')}",
                        f"  Deadline: {da.get('deadline','')}",
                        f"  Note: {da.get('note','')}",
                        f"  Apply: {da.get('application','')}",
                    ]
                    parts.append("\n".join(lines))
            elif is_pell:
                fed = data.get("federal", [])
                if fed:
                    p = fed[0]
                    lines = [
                        f"Federal Pell Grant: {p.get('description','')}",
                        f"  Amount: {p.get('amount','')}",
                        f"  Deadline: {p.get('deadline','')}",
                        f"  Note: {p.get('note','')}",
                    ]
                    parts.append("\n".join(lines))
            elif is_jkc:
                private = data.get("privateAndIdentity", [])
                jkc = next((s for s in private if "cooke" in s.get("name","").lower()), None)
                if jkc:
                    lines = [
                        f"Jack Kent Cooke Foundation Transfer Scholarship:",
                        f"  {jkc.get('description','')}",
                        f"  Amount: {jkc.get('amount','')}",
                        f"  Deadline: {jkc.get('deadline','')}",
                        f"  Eligibility: {jkc.get('eligibility','')}",
                        f"  Note: {jkc.get('note','')}",
                    ]
                    parts.append("\n".join(lines))
            else:
                systemwide = data.get("ucSystemwide", [])
                if isinstance(systemwide, list):
                    for s in systemwide[:4]:
                        lines.append(f"  {s.get('name','')}: {s.get('description','')[:150]}")
                fed = data.get("federal", [])
                for f in fed[:1]:
                    lines.append(f"  {f.get('name','')}: {f.get('description','')[:120]}")
                transfer_specific = data.get("transferSpecific", [])
                if isinstance(transfer_specific, list):
                    for s in transfer_specific[:2]:
                        lines.append(f"  {s.get('name','')}: {s.get('description','')[:120]}")
                private = data.get("privateAndIdentity", [])
                for p in private[:2]:
                    lines.append(f"  {p.get('name','')}: {p.get('description','')[:120]}")
                note = data.get("aidStackingNote", "")
                if note:
                    lines.append(f"\nAid stacking: {note[:250]}")
                parts.append("\n".join(lines))

    # --- Application timeline ---
    if any(w in q for w in ["when", "deadline", "timeline", "apply by", "application date", "october", "november", "tag deadline", "when do i apply"]):
        data = _load("application_timeline.json")
        if data:
            cycle = data.get("annualCycle", {})
            critical = data.get("criticalDeadlines", {})
            lines = ["UC Transfer Application Timeline:"]
            if isinstance(cycle, dict):
                for month, desc in list(cycle.items())[:8]:
                    lines.append(f"  {month}: {str(desc)[:120]}")
            elif isinstance(cycle, list):
                for e in cycle[:8]:
                    if isinstance(e, dict):
                        month = e.get("month", e.get("date", ""))
                        action = e.get("action", e.get("event", e.get("description", "")))
                        lines.append(f"  {month}: {str(action)[:120]}")
            if critical:
                lines.append("\nCritical deadlines:")
                if isinstance(critical, dict):
                    for k, v in list(critical.items())[:5]:
                        lines.append(f"  {k}: {v}")
            parts.append("\n".join(lines))

    # --- Campus profiles ---
    if any(w in q for w in ["about uc", "campus", "profile", "location", "what is uc", "known for", "tell me about"]):
        data = _load("uc_profiles.json")
        if data:
            uc_full = _detect_uc_full(query)
            profile = data.get(uc_full) if uc_full else None
            if profile:
                lines = [f"{uc_full}:"]
                if profile.get("location"):
                    lines.append(f"  Location: {profile['location']}")
                if profile.get("setting"):
                    lines.append(f"  Setting: {profile['setting']}")
                if profile.get("tagParticipant") is not None:
                    lines.append(f"  TAG: {'Yes' if profile['tagParticipant'] else 'No'}")
                extra_keys = [k for k in profile if k not in ("id","shortName","nickname","location","academicSystem","totalUndergrads","setting","tagParticipant")]
                for k in extra_keys[:6]:
                    v = profile[k]
                    if isinstance(v, list):
                        lines.append(f"  {k}: {', '.join(str(x) for x in v[:4])}")
                    elif isinstance(v, str) and v:
                        lines.append(f"  {k}: {v[:150]}")
                parts.append("\n".join(lines))

    # --- Major requirements / Impacted majors ---
    if any(w in q for w in ["major requirement", "impacted major", "impacted", "competitive major",
                             "major prep", "major prereq", "selective major", "requirements for",
                             "prerequisites for", "what do i need for", "major selection"]):
        data = _load("major_requirements.json")
        if data:
            uc_short = _detect_uc_short(query)
            imp = data.get("impactedMajors", {})
            cr = data.get("campusRequirements", {})
            # impactedMajors uses "UC Los Angeles" instead of "UCLA"
            IMP_NAME_MAP = {
                "UCLA": "UC Los Angeles", "UC Berkeley": "UC Berkeley",
                "UC San Diego": "UC San Diego", "UC Davis": "UC Davis",
                "UC Irvine": "UC Irvine", "UC Riverside": "UC Riverside",
                "UC Santa Barbara": "UC Santa Barbara", "UC Santa Cruz": "UC Santa Cruz",
                "UC Merced": "UC Merced",
            }
            imp_key = IMP_NAME_MAP.get(uc_short) if uc_short else None
            if imp_key and imp_key in imp:
                campus_imp = imp[imp_key]
                lines = [f"Major competitiveness at {uc_short}:"]
                note = campus_imp.get("note", "")
                hs = campus_imp.get("highlySelective", [])
                if note:
                    lines.append(f"  {note[:280]}")
                if hs:
                    lines.append(f"  Most competitive majors: {', '.join(hs[:10])}")
                if uc_short in cr:
                    pages = cr[uc_short].get("pages", [])
                    for page in pages[:1]:
                        text = page.get("text", "")
                        if text and len(text) > 100:
                            clean = " ".join(text.split())[:600]
                            lines.append(f"\nAdmission requirements detail:\n  {clean}")
                parts.append("\n".join(lines))
            else:
                lines = ["Impacted major overview by UC campus:"]
                for uc, info in imp.items():
                    is_all = info.get("impacted", False)
                    top = info.get("highlySelective", [])[:3]
                    lines.append(
                        f"  {uc}: {'All majors competitive' if is_all else 'Some majors competitive'}"
                        + (f" — Top: {', '.join(top)}" if top else "")
                    )
                parts.append("\n".join(lines))

    # --- Major-specific admit rates ---
    if any(w in q for w in ["admit rate", "acceptance rate", "chances", "how hard", "competitive",
                             "selectiv", "get in", "major admit", "major rate", "rate for cs",
                             "rate for engineering", "rate for nursing", "rate for biology",
                             "rate for psychology", "rate for business", "what are my chances"]):
        major_data = _load("major_admit_rates.json")
        if major_data:
            uc_short = _detect_uc_short(query)
            campuses = major_data.get("campuses", {})

            # Try to detect a major from the query
            major_keywords = {
                "computer science": "Computer Science", "cs": "Computer Science",
                "electrical engineering": "Electrical Engineering", "eecs": "EECS (Electrical Engineering & CS)",
                "mechanical engineering": "Mechanical Engineering",
                "nursing": "Nursing", "nursing science": "Nursing Science", "nursing (sonph)": "Nursing (SONPH)",
                "biology": "Biology", "bio": "Biology",
                "biochemistry": "Biochemistry",
                "psychology": "Psychology",
                "economics": "Economics",
                "political science": "Political Science",
                "business": "Business Administration", "business economics": "Business Economics",
                "sociology": "Sociology",
                "english": "English",
                "history": "History",
                "statistics": "Statistics",
                "data science": "Data Science",
                "cognitive science": "Cognitive Science",
                "bioengineering": "Bioengineering",
                "environmental": "Environmental Studies",
                "public health": "Public Health",
            }
            detected_major = None
            for kw, major_name in major_keywords.items():
                if kw in q:
                    detected_major = major_name
                    break

            if uc_short and uc_short in campuses:
                campus_data = campuses[uc_short]
                majors = campus_data.get("majors", {})
                overall = campus_data.get("overallTransferRate", "?")
                if detected_major:
                    # Try to find the specific major
                    matched = next((v for k, v in majors.items() if detected_major.lower() in k.lower()), None)
                    major_key = next((k for k in majors if detected_major.lower() in k.lower()), None)
                    if matched and major_key:
                        lines = [
                            f"Transfer admit rate for {major_key} at {uc_short} (Fall 2025 approx.):",
                            f"  Major-specific rate: {matched.get('rate','?')}",
                            f"  Campus overall rate: {overall}",
                            f"  Notes: {matched.get('notes','')}",
                            f"  Source: UC Information Center public data — rates shift year to year.",
                        ]
                        parts.append("\n".join(lines))
                    else:
                        lines = [f"Major-specific transfer admit rates at {uc_short} (overall: {overall}):"]
                        for mname, mdata in list(majors.items())[:10]:
                            lines.append(f"  {mname}: {mdata.get('rate','?')}")
                        parts.append("\n".join(lines))
                else:
                    lines = [f"Major-specific transfer admit rates at {uc_short} (overall campus rate: {overall}):"]
                    for mname, mdata in list(majors.items())[:12]:
                        lines.append(f"  {mname}: {mdata.get('rate','?')}")
                    insights = major_data.get("keyInsights", [])
                    if insights:
                        lines.append(f"\nKey insight: {insights[0]}")
                    parts.append("\n".join(lines))
            elif detected_major:
                # Show rates for detected major across all campuses
                lines = [f"Transfer admit rate for {detected_major} across UC campuses (approx.):"]
                for campus_name, campus_data in campuses.items():
                    majors = campus_data.get("majors", {})
                    matched = next((v for k, v in majors.items() if detected_major.lower() in k.lower()), None)
                    if matched:
                        lines.append(f"  {campus_name}: {matched.get('rate','?')} — {matched.get('notes','')[:80]}")
                insights = major_data.get("keyInsights", [])
                if insights:
                    lines.append(f"\n{insights[0]}")
                parts.append("\n".join(lines))

    # --- ADT ---
    if any(w in q for w in ["adt", "associate degree", "aa-t", "as-t", "degree for transfer"]):
        data = _load("adt_programs.json")
        if data:
            info = data.get("info", {})
            desc = info.get("description", "")
            uc_note = info.get("ucNote", "")
            csu_note = info.get("csuNote", "")
            common = data.get("commonMajors", {})
            lines = ["ADT (Associate Degree for Transfer — AA-T or AS-T):"]
            if desc:
                lines.append(f"  {desc[:350]}")
            if uc_note:
                lines.append(f"\n  UC campuses: {uc_note[:250]}")
            if csu_note:
                lines.append(f"  CSU campuses: {csu_note[:200]}")
            if common:
                lines.append("\nCommon ADT majors by field:")
                for field, majors in list(common.items())[:7]:
                    lines.append(f"  {field}: {', '.join(majors[:5])}")
            parts.append("\n".join(lines))
        else:
            parts.append(
                "ADT (Associate Degree for Transfer — AA-T or AS-T):\n"
                "  Guarantees admission to CSU system (not necessarily the campus/major of choice).\n"
                "  UC campuses give priority consideration to ADT holders.\n"
                "  File for your ADT before applying — it strengthens your transfer application."
            )

    # --- Extracurriculars ---
    if any(w in q for w in ["extracurricular", "activities", "clubs", "what should i do", "what to do",
                             "how to stand out", "leadership", "internship", "volunteer", "research",
                             "phi theta kappa", "ptk", "honors program", "tap ", "transfer alliance",
                             "eops", "mesa", "puente", "umoja", "student government", "club",
                             "resume", "activities section", "awards", "what else can i do",
                             "what does uc look for", "beyond gpa", "beside gpa", "besides gpa"]):
        data = _load("extracurriculars.json")
        if data:
            uc_short = _detect_uc_short(query)
            high_value = data.get("high_value_for_all_transfers", [])
            major_specific = data.get("major_specific", {})
            special = data.get("special_cc_programs", [])
            act_tips = data.get("activities_section_tips", {})
            holistic = data.get("what_uc_weighs_holistically", {})

            # Try to detect a major for specific recommendations
            major_map = {
                "computer science": "Computer Science / Engineering",
                "cs": "Computer Science / Engineering",
                "engineering": "Computer Science / Engineering",
                "biology": "Biology / Pre-Med / Pre-Nursing",
                "pre-med": "Biology / Pre-Med / Pre-Nursing",
                "premed": "Biology / Pre-Med / Pre-Nursing",
                "pre med": "Biology / Pre-Med / Pre-Nursing",
                "nursing": "Nursing (direct entry programs)",
                "psychology": "Psychology / Social Work",
                "social work": "Psychology / Social Work",
                "business": "Business / Economics",
                "economics": "Business / Economics",
                "political science": "Political Science / Public Policy",
                "poli sci": "Political Science / Public Policy",
                "environmental": "Environmental Science",
                "education": "Education / Sociology",
                "sociology": "Education / Sociology",
            }
            detected_major = None
            for kw, mname in major_map.items():
                if kw in q:
                    detected_major = mname
                    break

            is_activities_section = any(w in q for w in ["activities section", "how to describe", "how to list", "awards section"])
            is_special_programs = any(w in q for w in ["phi theta kappa", "ptk", "eops", "mesa", "puente", "umoja", "tap ", "transfer alliance", "honors program"])

            lines = []
            if is_activities_section:
                lines = [
                    f"How to fill out the UC Activities & Awards section:",
                    f"  How many: {act_tips.get('how_many','')}",
                    f"\nWhat to include: {', '.join(act_tips.get('what_to_include',[])[:8])}",
                    f"\nHow to write descriptions:",
                ]
                for tip in act_tips.get("how_to_describe", []):
                    lines.append(f"  - {tip}")
                lines.append(f"\nWeak example: \"{act_tips.get('bad_example','')}\"")
                lines.append(f"Strong example: \"{act_tips.get('good_example','')}\"")
            elif is_special_programs:
                lines = ["Special CC programs that strengthen UC transfer applications:"]
                for prog in special:
                    lines.append(f"\n{prog.get('program','')} ({prog.get('priority','')} value):")
                    lines.append(f"  Who: {prog.get('who','')}")
                    lines.append(f"  What: {prog.get('what','')[:200]}")
                    if prog.get("important_note"):
                        lines.append(f"  IMPORTANT: {prog.get('important_note','')}")
            elif detected_major:
                lines = [f"Recommended extracurriculars for {detected_major} transfer applicants:"]
                activities = major_specific.get(detected_major, [])
                for a in activities:
                    lines.append(f"  • {a}")
                lines.append("\nHigh-value for ALL transfer students (regardless of major):")
                for hv in high_value[:5]:
                    lines.append(f"  • {hv.get('activity','')} [{hv.get('priority','')} priority]: {hv.get('why','')[:160]}")
            else:
                lines = ["Extracurriculars for UC transfer applicants — what matters most:"]
                for hv in high_value:
                    lines.append(f"\n• {hv.get('activity','')} [{hv.get('priority','')} priority]")
                    lines.append(f"  {hv.get('why','')[:200]}")
                    if hv.get("how_to_use"):
                        lines.append(f"  How: {hv.get('how_to_use','')[:150]}")
                factors = holistic.get("factors", [])
                if factors:
                    lines.append("\nWhat UC weighs holistically (beyond activities):")
                    for f in factors[:6]:
                        lines.append(f"  • {f}")
            parts.append("\n".join(lines))

    # --- Transfer tips / strategic advice ---
    if any(w in q for w in ["mistake", "tips", "advice", "strategy", "what should i know",
                             "waitlist", "waitlisted", "appeal", "rejected", "after admission",
                             "after i get", "after getting", "got admitted", "get admitted",
                             "housing", "sir ", "statement of intent", "additional comments",
                             "academic renewal", "grade forgiveness", "repeat a course", "retake",
                             "withdrawal", "w grade", "upward trend", "first gen", "first generation",
                             "low income", "common mistake", "did i mess up", "eop", "trio",
                             "cal grant", "blue and gold", "financial aid tips", "fafsa tips",
                             "alternate major", "second choice major", "what else", "what to know"]):
        tips = _load("transfer_tips.json")
        if tips:
            is_waitlist = any(w in q for w in ["waitlist", "waitlisted", "wait list"])
            is_grade = any(w in q for w in ["academic renewal", "grade forgiveness", "repeat", "retake", "w grade", "withdrawal"])
            is_after = any(w in q for w in ["after admission", "housing", "sir ", "statement of intent", "summer before", "orientation"])
            is_mistakes = any(w in q for w in ["mistake", "common mistake", "did i mess up", "what should i know", "tips", "advice"])
            is_firstgen = any(w in q for w in ["first gen", "first generation", "low income", "eop", "trio"])
            is_financial = any(w in q for w in ["cal grant", "blue and gold", "financial aid tips", "fafsa tips", "work study"])

            if is_waitlist:
                wl = tips.get("waitlist_strategy", {})
                lines = [
                    "Waitlist strategy:",
                    f"  What it means: {wl.get('what_waitlist_means','')}",
                    f"  Thin waitlists (rare movement): {', '.join(wl.get('historically_thin_waitlists',[]))}",
                    f"  More movement: {', '.join(wl.get('historically_more_movement',[]))}",
                    "\nWhat to do:",
                ]
                for a in wl.get("what_to_do", []):
                    lines.append(f"  • {a}")
                lines.append("\nLetter of Continued Interest (LOCI) tips:")
                for tip in wl.get("loci_tips", []):
                    lines.append(f"  • {tip}")
                parts.append("\n".join(lines))
            elif is_grade:
                gi = tips.get("grade_issues", {})
                ar = gi.get("academic_renewal", {})
                rep = gi.get("repeating_courses", {})
                wd = gi.get("withdrawal_grades", {})
                lines = [
                    "Dealing with bad grades as a transfer applicant:",
                    f"\nAcademic Renewal: {ar.get('what','')}",
                    f"  How: {ar.get('how','')}",
                    f"  Important: {ar.get('important','')}",
                    f"\nRepeating courses: {rep.get('what','')}",
                    f"  Strategy: {rep.get('strategy','')}",
                    f"\nW grades: {wd.get('what','')}",
                    f"  Exceptions: {wd.get('exceptions','')}",
                    f"  Rule: {wd.get('rule_of_thumb','')}",
                    f"\nUpward trend: {gi.get('upward_trend','')}",
                ]
                parts.append("\n".join(lines))
            elif is_after:
                aa = tips.get("after_admission", {})
                sir = aa.get("statement_of_intent_to_register", {})
                housing = aa.get("housing", {})
                summer = aa.get("summer_before_transfer", {})
                lines = [
                    "After UC admission — what to do:",
                    f"\nSIR (Statement of Intent to Register): {sir.get('what','')}",
                    f"  Deadline: {sir.get('deadline','')}",
                    f"  Note: {sir.get('note','')}",
                    f"\nHousing: {housing.get('urgency','')}",
                    f"  Reality: {housing.get('reality','')}",
                    "\nSummer before transfer:",
                    f"  DO NOT: {summer.get('do_not','')}",
                    "  DO:",
                ]
                for d in summer.get("do", []):
                    lines.append(f"    • {d}")
                parts.append("\n".join(lines))
            elif is_financial:
                fin = tips.get("financial_aid_tips", {})
                cg = fin.get("cal_grant", {})
                bg = fin.get("blue_and_gold", {})
                lines = [
                    "Financial aid tips for UC transfer students:",
                    f"\nCal Grant: {cg.get('what','')}",
                    f"  Eligibility: {cg.get('eligibility','')}",
                    f"  Deadline: {fin.get('priority_deadlines',{}).get('fafsa_cadaa','')}",
                    f"\nUC Blue and Gold: {bg.get('what','')}",
                    f"  How: {bg.get('how','')}",
                    f"\nAid stacking: {fin.get('stacking_aid','')}",
                ]
                parts.append("\n".join(lines))
            elif is_firstgen:
                fg = tips.get("first_gen_and_low_income", {})
                lines = [
                    f"First-generation and low-income transfer student resources:",
                    f"  {fg.get('note','')}",
                    "\nPrograms and resources:",
                ]
                for r in fg.get("resources", []):
                    lines.append(f"  • {r}")
                parts.append("\n".join(lines))
            else:
                # General tips — show common mistakes
                mistakes = tips.get("common_mistakes", [])
                facts = tips.get("lesser_known_facts", [])
                lines = ["Common mistakes UC transfer applicants make:"]
                for m in mistakes[:7]:
                    lines.append(f"\n• {m.get('mistake','')}")
                    lines.append(f"  Fix: {m.get('fix','')}")
                if facts:
                    lines.append("\nLesser-known transfer facts:")
                    for f in facts[:5]:
                        lines.append(f"  • {f}")
                parts.append("\n".join(lines))

    return "\n\n".join(parts) if parts else ""
