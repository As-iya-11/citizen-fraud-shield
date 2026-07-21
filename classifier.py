"""
classifier.py
A fast, transparent heuristic layer that runs BEFORE the RAG/LLM call.

Purpose: many scam patterns are identifiable from strong keyword/phrase signals alone.
Running this first gives:
- A near-instant preliminary signal (useful if the LLM call is slow or unavailable)
- An explainable, auditable trail of *why* something was flagged, independent of the LLM
- A second, independent detection layer -> matches the hackathon's evaluation focus on
  reducing false negatives while keeping the false-positive rate on citizen-facing tools
  very low.

This is intentionally simple (keyword/phrase matching with weighted categories) so it is
transparent and easy to explain in a demo -- not a black box. Keywords are grouped by
scam category, and each category includes common phrasing variants so that natural,
non-scripted descriptions of a scam (not just textbook phrasing) still get caught.
"""

from dataclasses import dataclass, field

HIGH_RISK_PHRASES = {
    # Digital arrest / fake law enforcement
    "digital arrest": 5,
    "cbi": 3,
    "enforcement directorate": 3,
    "ed officer": 3,
    "customs department": 2,
    "customs officer": 2,
    "trai": 2,
    "sim will be deactivated": 3,
    "sim card will be blocked": 3,
    "video call": 2,
    "stay on the call": 3,
    "stay on call": 3,
    "don't disconnect": 3,
    "do not disconnect": 3,
    "arrest warrant": 4,
    "will be arrested": 4,
    "avoid arrest": 4,
    "money laundering": 3,
    "verification account": 4,
    "safe account": 4,
    "refundable after verification": 4,
    "drugs in parcel": 3,
    "parcel with drugs": 3,
    "illegal parcel": 3,
    "illegal items": 2,
    "parcel was seized": 3,
    # Credential / OTP theft
    "otp": 3,
    "one time password": 3,
    "remote access": 4,
    "anydesk": 4,
    "teamviewer": 4,
    "quicksupport": 4,
    "share the otp": 4,
    "share your otp": 4,
    # Investment / lottery / prize
    "lottery": 2,
    "processing fee": 2,
    "customs fee": 2,
    "guaranteed returns": 3,
    "guaranteed daily returns": 3,
    "double your money": 3,
    "pay to unlock withdrawal": 4,
    "job task payment": 3,
    "advance fee": 3,
    # Isolation / secrecy tactics
    "don't tell anyone": 4,
    "do not tell anyone": 4,
    "don't tell your family": 4,
    "do not tell your family": 4,
    "keep this confidential": 3,
    # Extortion / blackmail / harassment
    "threatening": 3,
    "threatened": 3,
    "blackmail": 4,
    "morph": 4,
    "morphed": 4,
    "morphing": 4,
    "obscene": 3,
    "send them everywhere": 3,
    "share it with your contacts": 4,
    "share with your contacts": 4,
    "leak your photos": 4,
    "leak your pictures": 4,
    "pay double": 3,
    "pay more than i borrowed": 3,
    "calling my family": 3,
    "calling my contacts": 3,
    "harassing my family": 4,
    "recording of me": 3,
    "unless i pay": 3,
    "unless you pay": 3,
}

MEDIUM_RISK_PHRASES = {
    "urgent": 1,
    "immediately": 1,
    "right now": 1,
    "last chance": 2,
    "act now": 1,
    "account will be frozen": 2,
    "account will be blocked": 2,
    "account will be suspended": 2,
    "account suspended": 2,
    "kyc update": 2,
    "kyc will expire": 2,
    "kyc expire": 2,
    "update your kyc": 2,
    "click this link": 1,
    "click a link": 1,
    "click the link": 1,
    "enter your account details": 2,
    "enter my account details": 2,
    "install this app": 2,
    "install the app": 2,
    "loan app": 1,
    "took a loan": 1,
    "work from home": 1,
    "telegram group": 1,
    "whatsapp group": 1,
    "small registration fee": 2,
    "expire today": 1,
}


@dataclass
class HeuristicResult:
    score: int
    matched_phrases: list = field(default_factory=list)
    tier: str = "LOW"


NEGATION_CUES = [
    "didn't", "did not", "doesn't", "does not", "never", "wasn't", "was not",
    "isn't", "is not", "no request for", "without asking",
]


def _is_negated(text: str, phrase: str, window: int = 40) -> bool:
    """Checks whether a negation word appears shortly before the matched phrase
    in the same sentence, e.g. "didn't ask for my OTP" should NOT count as a
    positive OTP-request signal."""
    idx = text.find(phrase)
    if idx == -1:
        return False
    start = max(0, idx - window)
    preceding = text[start:idx]
    if "." in preceding:
        preceding = preceding.rsplit(".", 1)[-1]
    return any(cue in preceding for cue in NEGATION_CUES)


def score_message(message: str) -> HeuristicResult:
    text = message.lower()
    score = 0
    matched = []

    for phrase, weight in HIGH_RISK_PHRASES.items():
        if phrase in text and not _is_negated(text, phrase):
            score += weight
            matched.append((phrase, weight))

    for phrase, weight in MEDIUM_RISK_PHRASES.items():
        if phrase in text and not _is_negated(text, phrase):
            score += weight
            matched.append((phrase, weight))

    if score >= 6:
        tier = "HIGH"
    elif score >= 2:
        tier = "MEDIUM"
    else:
        tier = "LOW"

    return HeuristicResult(score=score, matched_phrases=matched, tier=tier)
