import json
import os
import re

# Non-PII capitalized words/phrases that might appear in tourism messages
SAFE_CAPITALIZED = {
    "Pura", "Vida", "Voyages", "San", "José", "Jose", "Arenal", "Tortuguero",
    "Manuel", "Antonio", "Tamarindo", "Quepos", "Heredia", "Limón", "Limon",
    "Escazú", "Escazu", "Puntarenas", "Alajuela", "Cartago", "Guanacaste",
    "Monteverde", "Jacó", "Jaco", "Corcovado", "Rincón", "Rincon", "Vieja",
    "Poás", "Poas", "Irazú", "Irazu", "Cahuita", "Puerto", "Viejo", "Dominical",
    "Uvita", "Nosara", "Sámara", "Samara", "Papagayo", "Osa", "Drake", "Bay",
    "Golfito", "Turrialba", "Sarapiquí", "Sarapiqui", "La", "Fortuna", "Pacuare",
    "Celeste", "Braulio", "Carrillo", "Tenorio", "Caño", "Cano", "Negro",
    "Hello", "Hi", "Dear", "Regards", "Sincerely", "Best", "Thanks", "Thank",
    "Warm", "Cheers", "Cordially", "Respectfully"
}

MONTHS_PATTERN = (
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December|"
    r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|"
    r"Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|Septiembre|Octubre|Noviembre|Diciembre)"
)


def redact_text(text: str) -> str:
    # 1. Protect Booking References (PV-#####) so no numeric/glued regex touches them
    booking_refs = {}

    def protect_ref(match):
        key = f"__BOOKING_REF_{len(booking_refs)}__"
        booking_refs[key] = match.group(0)
        return key

    text = re.sub(r"\bPV-[A-Za-z0-9]{5}\b", protect_ref, text)

    # Track discovered names, email local parts, phones, IDs, accounts, DOBs, and address chunks
    discovered_names = set()
    discovered_local_parts = set()
    discovered_digits = []  # (raw_digits, placeholder)
    discovered_address_chunks = set()

    # 2. Emails
    def replace_email(match):
        full_email = match.group(0)
        local_part = full_email.split("@")[0]
        discovered_local_parts.add(local_part)
        for part in re.split(r"[._\-0-9]+", local_part):
            if len(part) >= 3:
                discovered_names.add(part)
        return "[EMAIL]"

    text = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        replace_email,
        text
    )

    # 3. Bank Accounts (Costa Rican IBANs: CR + 20 digits, grouped or glued)
    def replace_iban(match):
        raw = re.sub(r"[\s-]+", "", match.group(0))
        discovered_digits.append((raw, "[ACCOUNT]"))
        return "[ACCOUNT]"

    text = re.sub(
        r"\bCR\d{2}(?:[\s-]?\d{4}){4}[\s-]?\d{2}\b",
        replace_iban,
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r"\bCR\d{18,22}\b",
        replace_iban,
        text,
        flags=re.IGNORECASE
    )

    # 4. Dates of Birth (Month-name, DD/MM/YYYY, YYYY-MM-DD)
    text = re.sub(
        rf"\b{MONTHS_PATTERN}\s+\d{{1,2}},?\s+\d{{4}}\b",
        "[DOB]",
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        rf"\b\d{{1,2}}\s+(?:de\s+)?{MONTHS_PATTERN}\s+(?:de\s+)?\d{{4}}\b",
        "[DOB]",
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r"\b(?:19|20)\d{2}[-/.](?:0[1-9]|1[0-2])[-/.](?:0[1-9]|[12]\d|3[01])\b",
        "[DOB]",
        text
    )
    text = re.sub(
        r"\b(?:0?[1-9]|[12]\d|3[01])[/.-](?:0?[1-9]|1[0-2])[/.-](?:19|20)\d{2}\b",
        "[DOB]",
        text
    )
    text = re.sub(
        r"(\bdate of birth is )([^,.\n]+)",
        r"\1[DOB]",
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r"(\bborn on )([^,.\n]+)",
        r"\1[DOB]",
        text,
        flags=re.IGNORECASE
    )

    # 5. National IDs (Cédula: 1-2345-6789 or 9 glued digits starting 1-9)
    def replace_id(match):
        digits = re.sub(r"\D", "", match.group(0))
        if len(digits) == 9:
            discovered_digits.append((digits, "[ID]"))
        return "[ID]"

    text = re.sub(r"\b[1-9]-\d{4}-\d{4}\b", replace_id, text)
    text = re.sub(r"\b[1-9]\s\d{4}\s\d{4}\b", replace_id, text)
    text = re.sub(
        r"(c[eé]dula(?:\s+number)?\s+is\s+)([0-9-\s]{9,13})\b",
        lambda m: m.group(1) + replace_id(m),
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(r"\b[1-9]\d{8}\b", replace_id, text)

    # 6. Phone Numbers (+506 8712-3456, 8712-3456, glued 8-digit or 11-digit with 506)
    def replace_phone(match):
        digits = re.sub(r"\D", "", match.group(0))
        if len(digits) >= 8:
            discovered_digits.append((digits[-8:], "[PHONE]"))
            discovered_digits.append((digits, "[PHONE]"))
        return "[PHONE]"

    text = re.sub(
        r"(?:\+?506[\s-]?)?\b[2-8]\d{3}[\s-]?\d{4}\b",
        replace_phone,
        text
    )

    # 7. Postal Addresses (Costa Rican style & contextual phrases)
    def record_address(addr_str: str) -> str:
        for chunk in addr_str.split(","):
            c = chunk.strip(" .,;:!?")
            if len(c) >= 5 and c not in SAFE_CAPITALIZED:
                discovered_address_chunks.add(c)
        return "[ADDRESS]"

    text = re.sub(
        r"(Please add the pickup at )(.+?)( to our booking)",
        lambda m: m.group(1) + record_address(m.group(2)) + m.group(3),
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r"(\bpickup at )((?:Avenida|Calle|Boulevard|Diagonal|Ruta|Barrio|Urbanizaci[oó]n|Residencial)[^.\n]+?)(\s+to our\b|\s+and keep\b|\.)",
        lambda m: m.group(1) + record_address(m.group(2)) + m.group(3),
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r"(Please send the paperwork to )([^.\n]+)(\.)",
        lambda m: m.group(1) + record_address(m.group(2)) + m.group(3),
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r"(send the written reply to )([^.\n]+)(\.)",
        lambda m: m.group(1) + record_address(m.group(2)) + m.group(3),
        text,
        flags=re.IGNORECASE
    )
    cr_address_pattern = (
        r"\b(?:Avenida|Calle|Boulevard|Paseo|Ruta|Barrio|Urbanizaci[oó]n|Residencial)\s+\d+[A-Za-z]?"
        r"\s*,\s*(?:Frente\s+a|Contiguo\s+a|Costado\s+\w+\s+de|Del?\s+\w+|\d+\s*m(?:etros)?\s+(?:norte|sur|este|oeste)\s+de)[^.\n]+"
    )
    text = re.sub(
        cr_address_pattern,
        lambda m: record_address(m.group(0)),
        text,
        flags=re.IGNORECASE
    )

    # 8. Person Names (Contextual & Signatures - using capture groups instead of variable-length lookbehinds)
    name_token = r"[A-ZÁÉÍÓÚÑÜ][a-záéíóúñü]+"
    full_name_pat = rf"{name_token}(?:\s+{name_token}){{1,3}}"

    def record_name_str(full: str) -> str:
        for word in full.strip().split():
            clean_w = word.strip(".,;:!?")
            if clean_w and clean_w not in SAFE_CAPITALIZED:
                discovered_names.add(clean_w)
        return "[NAME]"

    # "My name is <Name>" / "I am <Name>" / "This is <Name>"
    text = re.sub(
        rf"(\b(?:[Mm]y name is|I am|[Tt]his is)\s+)({full_name_pat})",
        lambda m: m.group(1) + record_name_str(m.group(2)),
        text
    )

    # Family / companion patterns: "My <relation> <Name>" or "with my <relation> <Name>"
    relations = (
        r"(?:son|daughter|wife|husband|partner|brother|sister|mother|father|"
        r"friend|colleague|cousin|uncle|aunt|nephew|niece|fianc[eé]|fianc[eé]e|spouse|companion)"
    )
    text = re.sub(
        rf"(\b(?:[Mm]y|with my)\s+{relations}\s+)({full_name_pat})",
        lambda m: m.group(1) + record_name_str(m.group(2)),
        text
    )

    # "<Name> will travel with me"
    text = re.sub(
        rf"({full_name_pat})(\s+will travel with me\b)",
        lambda m: record_name_str(m.group(1)) + m.group(2),
        text
    )

    # Sign-offs: "Regards,", "Best,", "Sincerely,", etc. followed by a newline and a Name
    signoffs = (
        r"(?:[Rr]egards|[Bb]est regards|[Kk]ind regards|[Ww]arm regards|[Ss]incerely|[Bb]est|"
        r"[Tt]hanks|[Tt]hank you|[Cc]heers|[Cc]ordially|[Rr]espectfully|[Ww]armly)"
    )
    text = re.sub(
        rf"({signoffs},?[ \t]*\r?\n)({full_name_pat})",
        lambda m: m.group(1) + record_name_str(m.group(2)),
        text
    )

    # 9. Second pass: Scrub any remaining occurrences of discovered names, email local parts, address chunks, or glued digits
    def strip_accents(s: str) -> str:
        replacements = str.maketrans("áéíóúñüÁÉÍÓÚÑÜ", "aeiounuAEIOUNU")
        return s.translate(replacements)

    def make_accent_insensitive_regex(word: str) -> str:
        base = strip_accents(word.lower())
        char_map = {
            "a": "[aáAÁ]",
            "e": "[eéEÉ]",
            "i": "[iíIÍ]",
            "o": "[oóOÓ]",
            "u": "[uúüUÚÜ]",
            "n": "[nñNÑ]",
        }
        return "".join(char_map.get(ch, re.escape(ch)) for ch in base)

    for chunk in sorted(discovered_address_chunks, key=len, reverse=True):
        text = re.sub(re.escape(chunk), "[ADDRESS]", text, flags=re.IGNORECASE)

    for raw_digits, placeholder in discovered_digits:
        if len(raw_digits) >= 8:
            text = re.sub(rf"\b{re.escape(raw_digits)}\b", placeholder, text, flags=re.IGNORECASE)

    for local_part in sorted(discovered_local_parts, key=len, reverse=True):
        if len(local_part) >= 3:
            text = re.sub(rf"\b{re.escape(local_part)}\b", "[EMAIL]", text, flags=re.IGNORECASE)

    for name_part in sorted(discovered_names, key=len, reverse=True):
        if len(name_part) >= 3 and name_part not in SAFE_CAPITALIZED:
            pat = make_accent_insensitive_regex(name_part)
            text = re.sub(rf"\b{pat}\b", "[NAME]", text)

    # Collapse consecutive identical placeholders if tokens were replaced next to each other
    text = re.sub(r"\[NAME\](?:\s+\[NAME\])+", "[NAME]", text)
    text = re.sub(r"\[ADDRESS\](?:\s*,?\s*\[ADDRESS\])+", "[ADDRESS]", text)

    # 10. Restore Booking References
    for key, val in booking_refs.items():
        text = text.replace(key, val)

    return text


def process_file(input_filename: str, output_filename: str) -> None:
    with open(input_filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    redacted_documents = {}
    for doc in data.get("documents", []):
        doc_id = doc["id"]
        raw_text = doc.get("text", "")
        redacted_text = redact_text(raw_text)
        if not redacted_text.strip():
            redacted_text = "[REDACTED]"
        redacted_documents[doc_id] = redacted_text

    output_data = {"redacted_documents": redacted_documents}
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)


def main() -> None:
    if os.path.exists("test-input.json"):
        process_file("test-input.json", "test-output.json")
    elif os.path.exists("train-input.json"):
        process_file("train-input.json", "test-output.json")


if __name__ == "__main__":
    main()
