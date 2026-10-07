"""Lightweight multilingual/NLP helpers for the Gold Purity project.

No external translation API is required. The web UI and project assistant use
these mappings to understand common English/Telugu/Hindi shop terminology.
"""

SUPPORTED_LANGUAGES = {"en", "te", "hi"}
SPEECH_LANGUAGES = {"en": "en-IN", "te": "te-IN", "hi": "hi-IN"}

COMMON_TERMS = {
    "బంగారం": "gold", "స్వచ్ఛత": "purity", "ఎంత": "what is", "ఏమిటి": "what is",
    "ప్రాజెక్ట్": "project", "డేటాసెట్": "dataset", "మోడల్": "model", "మోడళ్లు": "models",
    "అంచనా": "prediction", "సాంద్రత": "density", "రాగి": "copper", "వెండి": "silver",
    "జింక్": "zinc", "నికెల్": "nickel", "ఉష్ణోగ్రత": "temperature", "బరువు": "weight",
    "రిఫరెన్స్": "reference", "గ్రాఫ్": "graph", "గ్రాఫ్‌లు": "graphs", "నివేదిక": "report",
    "నివేదికలు": "reports", "చరిత్ర": "history", "ఎలా పనిచేస్తుంది": "how does it work",
    "ఎందుకు": "why", "హలో": "hello", "నమస్కారం": "hello",
    "सोना": "gold", "शुद्धता": "purity", "कितनी": "what is", "क्या": "what",
    "क्या है": "what is", "प्रोजेक्ट": "project", "डेटासेट": "dataset", "मॉडल": "model",
    "मॉडल्स": "models", "अनुमान": "prediction", "घनत्व": "density", "तांबा": "copper",
    "चाँदी": "silver", "चांदी": "silver", "जस्ता": "zinc", "निकेल": "nickel",
    "तापमान": "temperature", "वजन": "weight", "संदर्भ": "reference", "ग्राफ": "graph",
    "ग्राफ़": "graphs", "रिपोर्ट": "report", "इतिहास": "history", "कैसे काम करता है": "how does it work",
    "क्यों": "why", "नमस्ते": "hello",
}


def normalize_user_text(text: str) -> str:
    out = text or ""
    for src, dst in sorted(COMMON_TERMS.items(), key=lambda item: len(item[0]), reverse=True):
        out = out.replace(src, dst)
    return out
