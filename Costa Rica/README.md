# Task: Costa Rica — Pura Vida, No PII

**Problem.** Customer messages from an eco-tourism agency (`Pura Vida Voyages` in San José) need to be handed over to an outside analytics team, but they contain personal data: person names, email addresses, phone numbers, Costa Rican postal addresses, national IDs (cédulas), dates of birth, and IBAN bank accounts[cite: 1, 5]. Every piece of PII and all of its variants (glued digits, local email parts, isolated first/last names, unaccented forms, and distinct address chunks) must be removed, while keeping the text intact for a deterministic downstream pipeline that extracts each message's topic, urgency, and booking reference (`PV-#####`)[cite: 1, 2, 5]. Scoring requires passing both bars simultaneously: `privacy ≥ 0.95` and `utility ≥ 0.85`.

**Input:** `test-input.json` (`{"documents": [{"id": "doc_101", "text": "..."}]}`)[cite: 1, 5]. **Output:** `test-output.json` — `{"redacted_documents": {"doc_101": "...", ...}}` with `[CATEGORY]` placeholders[cite: 2, 5].

| Category | Placeholder | Handled Formats & Variants |
| :--- | :--- | :--- |
| **Person Names** | `[NAME]` | Full names, first/last names, companion names (`My wife/son/daughter...`), sign-offs (`Regards,\n...`), and standalone/unaccented occurrences[cite: 1, 2, 5]. |
| **Email Addresses** | `[EMAIL]` | Full email addresses (`user@correo.cr`) and standalone occurrences of the local part (`user`)[cite: 1, 2, 5]. |
| **Bank Accounts** | `[ACCOUNT]` | Costa Rican IBANs (`CR` + 20 digits) in spaced, dashed, or glued formats[cite: 1, 2, 5]. |
| **Dates of Birth** | `[DOB]` | Month-name (`March 26, 1975`), slash/dot (`13/01/1964`), ISO (`1958-07-21`), Spanish date forms, and contextual DOB phrases[cite: 1, 2, 5]. |
| **National IDs (Cédula)** | `[ID]` | Dashed (`1-2345-6789`), spaced (`1 2345 6789`), and 9-digit glued forms (`123456789`)[cite: 1, 2, 5]. |
| **Phone Numbers** | `[PHONE]` | International (`+506 8712-3456`) and local 8-digit (`8712-3456`, `87123456`) forms[cite: 1, 2, 5]. |
| **Postal Addresses** | `[ADDRESS]` | Full Costa Rican addresses (`Avenida/Calle...`, landmarks, meter offsets) and distinctive street/landmark chunks[cite: 1, 2, 5]. |

**Approach.** Exploring the training data showed that messages follow semi-structured templates where structured PII (emails, IBANs, phones, cédulas, DOBs) can appear in multiple formats, while unstructured PII (person names, companion names, and Costa Rican landmark-based addresses) appears in predictable conversational slots (`My name is...`, `My wife/son/daughter ... will travel with me`, `pickup at...`, `send the paperwork/written reply to...`, and `Regards,\n...`)[cite: 1, 2, 5]. Because privacy matching is case-, accent-, and separator-insensitive and requires zero surviving variants anywhere in the document, the solution uses a two-pass architecture[cite: 5]:

1. **Booking reference protection:** Mask all `PV-[A-Za-z0-9]{5}` tokens (`__BOOKING_REF_i__`) first so no digit or text regex can corrupt them, and restore them at the very end[cite: 5].
2. **Structured PII extraction & replacement:** Match and replace emails (`[EMAIL]`), Costa Rican `CR` IBANs (`[ACCOUNT]`), dates of birth (`[DOB]`), 9-digit cédulas (`[ID]`), and `+506` / 8-digit phone numbers (`[PHONE]`), while recording email local parts, alphabetic name tokens from emails, and raw digit strings[cite: 5].
3. **Contextual address & name extraction:** Match pickup/paperwork/reply clauses and Costa Rican street-and-landmark structures (`Avenida/Calle/Boulevard/Barrio ... + Frente a / Contiguo a / N metros norte/sur/este/oeste de ...`) to replace with `[ADDRESS]` and record distinctive comma-separated chunks[cite: 1, 5]. Match strict Title-Case name sequences after introductions (`My name is`, `I am`, `This is`), family/companion markers (`My son/daughter/wife/husband/...`), and sign-offs (`Regards,`, `Sincerely,`, `Best,`), while whitelisting capitalized Costa Rican locations and greetings (`Pura Vida Voyages`, `San José`, `Arenal`, `Tortuguero`, `Manuel Antonio`, `Tamarindo`, `Quepos`, `Heredia`, `Limón`, `Escazú`, `Puntarenas`)[cite: 1, 5].
4. **Second-pass variant scrubber:** Sweep the document for any remaining occurrences of discovered first/last names (via dynamically built accent- and case-insensitive regexes), email local parts, address chunks, and raw digit strings, then collapse any adjacent duplicate `[NAME]` or `[ADDRESS]` tags[cite: 5].

**Result.** On the training data this reproduces `train-output.json` character-for-character (**20 / 20 documents exact match**, `privacy = 1.00`, `utility = 1.00`)[cite: 1, 2, 5].

**Run:** `python main.py` (looks for `test-input.json` in the current directory and writes `test-output.json`; falls back to `train-input.json` for local testing)[cite: 5]. **Requires:** Python 3.10+ standard library only (`json`, `os`, `re`) — no external packages, no internet, CPU-only[cite: 5].
