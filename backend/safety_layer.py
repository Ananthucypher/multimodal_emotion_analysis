"""
MIRO Safety Layer - P0 Implementation
======================================
Provides:
1. Crisis Detection - Keyword-based high-risk signal detection
2. Therapeutic Verifier - Non-diagnostic language enforcement
3. Safety Filter - Audits all LLM output before delivery

Per Execution Blueprint Section 8.
"""
import re
import logging
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ============================================================
# CRISIS DETECTION
# ============================================================

CRISIS_KEYWORDS = {
    "explicit": [
        "suicide", "kill myself", "end my life", "want to die",
        "self-harm", "hurt myself", "cutting myself", "take my life",
        "not worth living", "better off dead", "end it all"
    ],
    "implicit": [
        "no point anymore", "better off without me", 
        "can't go on", "giving up", "final goodbye",
        "nobody would miss me", "tired of living",
        "don't want to be here", "disappear forever"
    ]
}

CRISIS_RESOURCES = {
    "US": {
        "name": "National Suicide Prevention Lifeline",
        "phone": "988",
        "text": "Text HOME to 741741"
    },
    "International": {
        "name": "International Association for Suicide Prevention",
        "url": "https://www.iasp.info/resources/Crisis_Centres/"
    }
}


@dataclass
class CrisisDetectionResult:
    """Result of crisis keyword detection."""
    level: str  # "NONE", "HIGH", "CRITICAL"
    matched_keyword: Optional[str] = None
    keyword_type: Optional[str] = None  # "explicit" or "implicit"
    confidence: float = 0.0
    
    @property
    def is_crisis(self) -> bool:
        return self.level in ("HIGH", "CRITICAL")
    
    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "matched_keyword": self.matched_keyword,
            "type": self.keyword_type,
            "is_crisis": self.is_crisis
        }


def detect_crisis(text: str) -> CrisisDetectionResult:
    """
    Detect crisis signals in text using keyword matching.
    
    Args:
        text: The transcript or user input to analyze
        
    Returns:
        CrisisDetectionResult with level and matched keyword
    """
    if not text:
        return CrisisDetectionResult(level="NONE")
    
    text_lower = text.lower()
    
    # Check explicit keywords first (higher priority)
    for keyword in CRISIS_KEYWORDS["explicit"]:
        if keyword in text_lower:
            logger.warning(f"CRITICAL crisis keyword detected: '{keyword}'")
            return CrisisDetectionResult(
                level="CRITICAL",
                matched_keyword=keyword,
                keyword_type="explicit",
                confidence=0.95
            )
    
    # Check implicit keywords
    for keyword in CRISIS_KEYWORDS["implicit"]:
        if keyword in text_lower:
            logger.warning(f"HIGH crisis keyword detected: '{keyword}'")
            return CrisisDetectionResult(
                level="HIGH",
                matched_keyword=keyword,
                keyword_type="implicit",
                confidence=0.75
            )
    
    return CrisisDetectionResult(level="NONE")


def get_crisis_response(crisis_result: CrisisDetectionResult) -> dict:
    """
    Generate appropriate crisis response based on detection level.
    """
    if crisis_result.level == "CRITICAL":
        return {
            "override_response": True,
            "message": (
                "I'm really concerned about what you're sharing. "
                "Please reach out to a crisis helpline right now. "
                "You don't have to face this alone."
            ),
            "resources": CRISIS_RESOURCES,
            "halt_therapeutic": True
        }
    
    elif crisis_result.level == "HIGH":
        return {
            "override_response": False,
            "prepend_message": "I want to check in—are you safe right now? ",
            "append_resources": True,
            "resources": CRISIS_RESOURCES,
            "halt_therapeutic": False
        }
    
    return {"override_response": False, "halt_therapeutic": False}


# ============================================================
# NON-DIAGNOSTIC LANGUAGE ENFORCEMENT
# ============================================================

# Patterns that should be blocked or rewritten
DIAGNOSTIC_PATTERNS = [
    # Direct diagnostic language
    (r'\byou have\s+(depression|anxiety|PTSD|bipolar|disorder)', "rewrite"),
    (r'\byou are\s+(depressed|anxious|mentally ill)', "rewrite"),
    (r'\bdiagnos(is|ed|e|ing)\b', "flag"),
    (r'\bdisorder\b', "flag"),
    (r'\bsymptoms?\s+of\b', "flag"),
    (r'\btreatment\s+for\b', "flag"),
    (r'\bcondition\b', "flag"),
    
    # Medical advice
    (r'\b(should|need to)\s+see\s+a\s+(doctor|psychiatrist|therapist)', "soften"),
    (r'\bmedication\b', "flag"),
    (r'\bprescri(be|ption)\b', "block"),
    
    # Authoritative phrasing
    (r'\bthis\s+indicates\s+that\s+you\b', "rewrite"),
    (r'\byou\s+are\s+suffering\s+from\b', "rewrite"),
    (r'\bsigns\s+of\s+(depression|anxiety|mental)', "flag"),
]

# Replacement suggestions for common issues
REPLACEMENTS = {
    "you have depression": "you may be experiencing low mood",
    "you have anxiety": "you appear to be feeling anxious",
    "you are depressed": "you seem to be feeling down",
    "you are anxious": "you appear to be experiencing worry",
    "symptoms of": "patterns that might suggest",
    "treatment for": "approaches that may help with",
    "this indicates that you": "this might suggest",
    "you are suffering from": "you may be experiencing",
    "signs of depression": "indicators of low mood",
    "signs of anxiety": "indicators of elevated stress",
}


@dataclass
class VerificationResult:
    """Result of therapeutic verification."""
    passed: bool
    original_text: str
    verified_text: str
    issues_found: List[str]
    rewrites_applied: int
    
    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "issues_found": self.issues_found,
            "rewrites_applied": self.rewrites_applied
        }


def verify_therapeutic_response(text: str) -> VerificationResult:
    """
    Verify and sanitize LLM therapeutic response.
    
    Enforces non-diagnostic language and appropriate phrasing.
    Returns verified (possibly modified) text.
    """
    if not text:
        return VerificationResult(
            passed=True,
            original_text="",
            verified_text="",
            issues_found=[],
            rewrites_applied=0
        )
    
    issues = []
    modified_text = text
    rewrites = 0
    
    # Check each diagnostic pattern
    for pattern, action in DIAGNOSTIC_PATTERNS:
        matches = re.findall(pattern, modified_text, re.IGNORECASE)
        if matches:
            issue = f"Found '{matches[0]}' (action: {action})"
            issues.append(issue)
            logger.info(f"Safety filter: {issue}")
            
            if action == "block":
                # Completely block this response
                return VerificationResult(
                    passed=False,
                    original_text=text,
                    verified_text="I want to support you, but I'm not sure how to respond helpfully right now. If you're struggling, please consider reaching out to someone you trust.",
                    issues_found=issues,
                    rewrites_applied=0
                )
    
    # Apply replacements
    for original, replacement in REPLACEMENTS.items():
        if original.lower() in modified_text.lower():
            # Case-insensitive replacement
            pattern = re.compile(re.escape(original), re.IGNORECASE)
            modified_text = pattern.sub(replacement, modified_text)
            rewrites += 1
    
    # Truncate if too long (>150 words is too verbose for therapeutic response)
    words = modified_text.split()
    if len(words) > 150:
        modified_text = ' '.join(words[:150]) + "..."
        issues.append("Truncated: Response exceeded 150 words")
    
    return VerificationResult(
        passed=len(issues) == 0 or rewrites > 0,
        original_text=text,
        verified_text=modified_text,
        issues_found=issues,
        rewrites_applied=rewrites
    )


# ============================================================
# COMBINED SAFETY FILTER
# ============================================================

def apply_safety_filter(
    transcript: str,
    llm_response: str
) -> Tuple[str, dict]:
    """
    Apply complete safety filter pipeline.
    
    1. Check transcript for crisis signals
    2. Verify LLM response for diagnostic language
    3. Return modified response with metadata
    
    Args:
        transcript: User's transcribed speech
        llm_response: Generated therapeutic response
        
    Returns:
        Tuple of (safe_response, safety_metadata)
    """
    metadata = {
        "crisis": None,
        "verification": None,
        "modified": False
    }
    
    # 1. Crisis Detection
    crisis_result = detect_crisis(transcript)
    metadata["crisis"] = crisis_result.to_dict()
    
    if crisis_result.is_crisis:
        crisis_response = get_crisis_response(crisis_result)
        
        if crisis_response.get("override_response"):
            # Critical crisis - return crisis resources only
            return (crisis_response["message"], metadata)
        
        elif crisis_response.get("prepend_message"):
            # High concern - prepend safety check
            llm_response = crisis_response["prepend_message"] + llm_response
    
    # 2. Therapeutic Verification
    verification = verify_therapeutic_response(llm_response)
    metadata["verification"] = verification.to_dict()
    metadata["modified"] = verification.rewrites_applied > 0
    
    # 3. Append crisis resources if needed
    if crisis_result.level == "HIGH":
        llm_response = verification.verified_text + (
            "\n\nIf you're having thoughts of self-harm, please reach out: "
            "Call 988 (Suicide & Crisis Lifeline) or text HOME to 741741."
        )
    else:
        llm_response = verification.verified_text
    
    return (llm_response, metadata)


# ============================================================
# PRE-SESSION DISCLOSURE
# ============================================================

PRE_SESSION_DISCLOSURE = """
MIRO is an AI emotional support tool. It is NOT a therapist, counselor, 
or medical professional. It cannot diagnose conditions or prescribe treatments.

This tool provides observational insights based on your emotional expression. 
All observations are meant for self-reflection only, not clinical interpretation.

For professional support, please consult a licensed mental health provider.

By continuing, you acknowledge these limitations.
"""


def get_disclosure() -> str:
    """Return the pre-session disclosure text."""
    return PRE_SESSION_DISCLOSURE.strip()
