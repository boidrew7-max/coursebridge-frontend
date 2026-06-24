import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

courses_path = os.path.join(
    BASE_DIR,
    "data",
    "all_transferable_courses.json"
)

with open(courses_path, "r", encoding="utf-8") as f:
    courses = json.load(f)


def search_courses(query):

    query = query.lower()

    matches = []

    # DETECT SCHOOL
    school_detected = None

    all_schools = set()

    for course in courses:

        if "school" in course:

            all_schools.add(
                course["school"]
            )

    # PRIORITIZE FULL SCHOOL NAME MATCHES
    for school in all_schools:

        school_lower = school.lower()

        # exact full phrase match
        if school_lower in query:

            school_detected = school_lower
            break

    # SECONDARY MATCHING
    if not school_detected:

        for school in all_schools:

            school_lower = school.lower()

            # remove common suffixes
            simplified = (
                school_lower
                .replace("college", "")
                .replace("community", "")
                .strip()
            )

            if simplified in query:

                school_detected = school_lower
                break

    # SUBJECT DETECTION
    subjects = [
        "math",
        "biology",
        "chemistry",
        "physics",
        "economics",
        "business",
        "computer",
        "english",
        "history",
        "psychology"
    ]

    subject_detected = None

    for subject in subjects:

        if subject in query:

            subject_detected = subject
            break

    # STRICT FILTERING
    for course in courses:

        searchable = ""

        for key, value in course.items():

            if isinstance(value, str):

                searchable += value.lower() + " "

        # REQUIRE SCHOOL MATCH
        if school_detected:

            if (
                "school" not in course
                or course["school"].lower()
                != school_detected
            ):
                continue

        # REQUIRE SUBJECT MATCH
        if subject_detected:

            if subject_detected not in searchable:
                continue

        matches.append(course)

    # REMOVE DUPLICATES
    unique_matches = []

    seen = set()

    for match in matches:

        key = (
            match.get("school", ""),
            match.get("prefix", ""),
            match.get("courseNumber", "")
        )

        if key not in seen:

            seen.add(key)

            unique_matches.append(match)

    return unique_matches[:20]