"""Basic medical-safety classification and reusable notices."""

EMERGENCY_TERMS = {
    "chest pain",
    "can't breathe",
    "cannot breathe",
    "difficulty breathing",
    "severe bleeding",
    "unconscious",
    "suicide",
    "overdose",
    "stroke",
    "seizure",
    "anaphylaxis",
    "বুকে ব্যথা",
    "শ্বাস নিতে পারছি না",
    "অজ্ঞান",
    "অতিরিক্ত রক্তপাত",
    "আত্মহত্যা",
}

DISCLAIMER = (
    "This chatbot provides educational information only and is not a diagnosis, "
    "prescription, or substitute for a qualified medical professional."
)

EMERGENCY_MESSAGE = (
    "Your message may describe a medical emergency. Contact local emergency services "
    "or go to the nearest emergency department now. In India, you can call 112. "
    "Do not rely on this chatbot for urgent care."
)


def has_emergency_language(text: str) -> bool:
    """Detect a small set of obvious emergency phrases."""

    normalized = text.casefold()
    return any(term in normalized for term in EMERGENCY_TERMS)
