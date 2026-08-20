from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from utils.logger import logger


class EnterprisePresidioAnalyzer:
    """Presidio ML-driven PII Analyzer with custom domain recognizers."""

    def __init__(self):
        # 1. Initialize Presidio's NLP-backed Analyzer Engine
        self.analyzer = AnalyzerEngine()

        # 2. Add Custom Enterprise Recognizer (e.g., Employee ID: EMP-123456)
        emp_id_pattern = Pattern(name="emp_id_pattern", regex=r"\bEMP-\d{6}\b", score=0.95)
        emp_id_recognizer = PatternRecognizer(
            supported_entity="ENTERPRISE_EMP_ID",
            patterns=[emp_id_pattern],
            context=["employee", "staff", "badge", "worker"]
        )
        self.analyzer.registry.add_recognizer(emp_id_recognizer)
        logger.info("[PRESIDIO] Initialized Analyzer Engine with Custom Employee ID Recognizer.")

    def analyze_text(self, text: str, score_threshold: float = 0.6) -> list:
        """Scans text for PII entities using NER and custom regex pattern recognizers."""
        if not text:
            return []

        results = self.analyzer.analyze(
            text=text,
            entities=[
                "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", 
                "IP_ADDRESS", "CREDIT_CARD", "ENTERPRISE_EMP_ID"
            ],
            language="en",
            score_threshold=score_threshold
        )
        return results


presidio_analyzer_service = EnterprisePresidioAnalyzer()