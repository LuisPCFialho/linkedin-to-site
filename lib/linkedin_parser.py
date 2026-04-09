"""Parse LinkedIn PDF exports into structured data.

Handles the standard LinkedIn "Save as PDF" format which has a two-column
layout: left sidebar (contact, skills, languages, certifications) and
main content (name, headline, experience, education).
"""
import re
import pdfplumber


# Section headers in PT and EN
SECTION_HEADERS_SIDEBAR = {
    "contact": ["Contato", "Contact", "Contact Info"],
    "skills": ["Principais competências", "Top Skills", "Skills"],
    "languages": ["Languages", "Idiomas"],
    "certifications": ["Certifications", "Certificações", "Certificados",
                       "Licenses & certifications"],
}

SECTION_HEADERS_MAIN = {
    "experience": ["Experiência", "Experience"],
    "education": ["Formação acadêmica", "Formação Académica", "Education"],
    "summary": ["Summary", "Resumo", "About"],
}

PAGE_RE = re.compile(r"^Page\s+\d+\s+of\s+\d+\s*$", re.IGNORECASE)

DURATION_RE = re.compile(
    r"\(\s*\d+\s*(?:ano|anos|year|years|mês|meses|month|months)"
    r"(?:\s*\d+\s*(?:mês|meses|month|months))?\s*\)",
    re.IGNORECASE,
)

DATE_RANGE_RE = re.compile(
    r"((?:janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|"
    r"novembro|dezembro|january|february|march|april|may|june|july|august|"
    r"september|october|november|december)\s+(?:de\s+)?\d{4})"
    r"\s*[-–]\s*"
    r"((?:janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|"
    r"novembro|dezembro|january|february|march|april|may|june|july|august|"
    r"september|october|november|december)\s+(?:de\s+)?\d{4}|Present|Presente|present|presente)",
    re.IGNORECASE,
)

LOCATION_RE = re.compile(
    r"^[A-ZÀ-Ú][a-zà-ú]+(?:[\s-][A-ZÀ-Ú]?[a-zà-ú]+)*,\s*[A-ZÀ-Ú][a-zà-ú]+"
    r"(?:[\s-][A-ZÀ-Ú]?[a-zà-ú]+)*(?:,\s*[A-ZÀ-Ú][a-zà-ú]+(?:[\s-][A-ZÀ-Ú]?[a-zà-ú]+)*)?$"
)


def _extract_columns(pdf_path):
    """Extract text split into left (sidebar) and right (main) columns using x-position."""
    left_lines = []
    right_lines = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            width = page.width
            # Threshold: ~35% of page width separates sidebar from main
            threshold = width * 0.35

            words = page.extract_words(
                x_tolerance=3, y_tolerance=3,
                keep_blank_chars=True, use_text_flow=False
            )

            if not words:
                continue

            # Group words into lines by y-position
            lines_by_y = {}
            for w in words:
                y_key = round(w["top"] / 3) * 3  # Group within 3pt
                if y_key not in lines_by_y:
                    lines_by_y[y_key] = []
                lines_by_y[y_key].append(w)

            for y_key in sorted(lines_by_y.keys()):
                line_words = sorted(lines_by_y[y_key], key=lambda w: w["x0"])

                left_words = [w for w in line_words if w["x0"] < threshold]
                right_words = [w for w in line_words if w["x0"] >= threshold]

                if left_words:
                    text = " ".join(w["text"] for w in left_words).strip()
                    if text and not PAGE_RE.match(text):
                        left_lines.append(text)

                if right_words:
                    text = " ".join(w["text"] for w in right_words).strip()
                    if text and not PAGE_RE.match(text):
                        right_lines.append(text)

    return left_lines, right_lines


def _find_section(line, headers_map):
    """Check if a line matches any section header."""
    for section, headers in headers_map.items():
        for header in headers:
            if line.strip().lower() == header.lower():
                return section
    return None


def _split_into_sections(lines, headers_map):
    """Split lines into named sections based on headers."""
    sections = {}
    current = "_header"
    sections[current] = []

    for line in lines:
        sec = _find_section(line, headers_map)
        if sec:
            current = sec
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(line)

    return sections


def _is_duration_line(line):
    return bool(re.match(
        r"^\d+\s+(?:ano|anos|year|years|mês|meses|month|months)"
        r"(?:\s+\d+\s+(?:mês|meses|month|months))?$",
        line.strip(), re.IGNORECASE
    ))


def _is_date_range(line):
    return bool(DATE_RANGE_RE.search(line))


def _is_location(line):
    return bool(LOCATION_RE.match(line.strip()))


def _parse_contact(lines):
    contact = {"email": "", "linkedin": "", "location": ""}
    for line in lines:
        line = line.strip()
        if "@" in line and "." in line:
            contact["email"] = line
        elif "linkedin.com" in line.lower():
            url = line
            if not url.startswith("http"):
                url = "https://www." + url
            contact["linkedin"] = url
        elif "(LinkedIn)" in line:
            continue
        elif _is_location(line):
            contact["location"] = line
    return contact


def _parse_skills(lines):
    return [l.strip() for l in lines if l.strip()]


def _parse_languages(lines):
    langs = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        match = re.match(r"(.+?)\s*\((.+?)\)", line)
        if match:
            langs.append({"name": match.group(1).strip(), "level": match.group(2).strip()})
        else:
            langs.append({"name": line, "level": ""})
    return langs


def _parse_certifications(lines):
    return [l.strip() for l in lines if l.strip()]


def _parse_header_and_experience(main_sections):
    """Parse header (name/title/location) and experience from main content."""
    header = main_sections.get("_header", [])

    name = ""
    title = ""
    location = ""

    for line in header:
        line = line.strip()
        if not line:
            continue
        if not name:
            name = line
        elif not title:
            title = line
        elif _is_location(line):
            location = line

    return name, title, location


def _parse_experience(lines):
    """Parse experience entries from the experience section."""
    entries = []
    current_company = None
    current_entry = None
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        # Skip pure duration lines (company total)
        if _is_duration_line(line):
            i += 1
            continue

        # Date range line -> belongs to current entry
        if _is_date_range(line):
            if current_entry:
                current_entry["date"] = DURATION_RE.sub("", line).strip()
            i += 1
            continue

        # Location line
        if _is_location(line) and current_entry and current_entry.get("date"):
            current_entry["location"] = line
            i += 1
            continue

        # Look ahead to determine what this line is
        next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
        next_is_date = _is_date_range(next_line)
        next_is_dur = _is_duration_line(next_line)

        if next_is_date:
            # This is a role title
            if current_entry:
                entries.append(current_entry)
            current_entry = {
                "role": line, "company": current_company or "",
                "date": "", "location": "", "description": "",
            }
        elif next_is_dur:
            # This is a company name
            current_company = line
        else:
            # Could be description text or a company/role
            if current_entry and current_entry.get("date"):
                # Likely description
                if current_entry["description"]:
                    current_entry["description"] += " " + line
                else:
                    current_entry["description"] = line
            else:
                # Check if two lines ahead is a duration
                line_after_next = lines[i + 2].strip() if i + 2 < len(lines) else ""
                if _is_duration_line(line_after_next):
                    current_company = line
                elif current_company and not current_entry:
                    # Standalone company with no clear role yet
                    current_company = line
                else:
                    # Likely a company name
                    current_company = line

        i += 1

    if current_entry:
        entries.append(current_entry)

    return entries


def _parse_education(lines):
    entries = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        school = line
        course = ""
        date = ""

        if i + 1 < len(lines):
            next_l = lines[i + 1].strip()
            # Pattern: "Course, Field · (dates)"
            match = re.match(r"(.+?)\s*·\s*\((.+?)\)", next_l)
            if match:
                course = match.group(1).strip()
                date = match.group(2).strip()
                i += 2
            elif _is_date_range(next_l):
                date = DURATION_RE.sub("", next_l).strip()
                i += 2
            else:
                course = next_l
                if i + 2 < len(lines):
                    third = lines[i + 2].strip()
                    m2 = re.match(r"\((.+?)\)", third)
                    if m2:
                        date = m2.group(1).strip()
                        i += 3
                    else:
                        i += 2
                else:
                    i += 2
        else:
            i += 1

        entries.append({"school": school, "course": course, "date": date})

    return entries


def parse_linkedin_pdf(pdf_path):
    """
    Parse a LinkedIn PDF export into structured data.

    Uses positional text extraction to separate the sidebar (contact, skills,
    languages, certifications) from the main content (name, experience, education).
    """
    left_lines, right_lines = _extract_columns(pdf_path)

    # Parse sidebar sections
    sidebar = _split_into_sections(left_lines, SECTION_HEADERS_SIDEBAR)
    contact = _parse_contact(sidebar.get("contact", []))
    skills = _parse_skills(sidebar.get("skills", []))
    languages = _parse_languages(sidebar.get("languages", []))
    certifications = _parse_certifications(sidebar.get("certifications", []))

    # Parse main content sections
    main = _split_into_sections(right_lines, SECTION_HEADERS_MAIN)
    name, title, location = _parse_header_and_experience(main)
    experience = _parse_experience(main.get("experience", []))
    education = _parse_education(main.get("education", []))

    # Summary
    summary_lines = main.get("summary", [])
    summary = " ".join(l.strip() for l in summary_lines if l.strip())

    # Fill location from contact if missing
    if not location and contact.get("location"):
        location = contact["location"]

    return {
        "name": name,
        "title": title,
        "location": location,
        "email": contact.get("email", ""),
        "linkedin": contact.get("linkedin", ""),
        "website": "",
        "summary": summary,
        "experience": experience,
        "education": education,
        "skills": skills,
        "languages": languages,
        "certifications": certifications,
    }
