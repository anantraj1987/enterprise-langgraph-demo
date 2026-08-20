# presidio_governance/anonymizer.py

import uuid
from typing import Tuple, Dict
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from presidio_governance.analyzer import presidio_analyzer_service
from utils.logger import logger


class PresidioReversibleAnonymizer:
    """Anonymizes text with deterministic tokens and supports reverse re-hydration."""

    def __init__(self):
        # Initialize Presidio's Anonymizer Engine
        self.anonymizer = AnonymizerEngine()

    def anonymize_and_map(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Detects PII via Presidio Analyzer and replaces matches with reversible session tokens.
        
        Returns:
            Tuple[anonymized_text, token_to_real_value_map]
        """
        if not text:
            return text, {}

        # 1. Run Presidio Analyzer
        analysis_results = presidio_analyzer_service.analyze_text(text)
        if not analysis_results:
            return text, {}

        token_map: Dict[str, str] = {}
        operators: Dict[str, OperatorConfig] = {}

        # 2. Build custom replacement tokens per entity detected
        for result in analysis_results:
            entity_type = result.entity_type
            real_val = text[result.start:result.end]
            
            # Generate unique session token ID
            token_id = str(uuid.uuid4())[:6]
            token = f"<ANON_{entity_type}_{token_id}>"
            
            # Save mapping: Token -> Real Raw Value
            token_map[token] = real_val
            
            # Assign Presidio replacement operator for this entity type
            operators[entity_type] = OperatorConfig("replace", {"new_value": token})

        # 3. Anonymize input text using Presidio Anonymizer
        anonymized_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=analysis_results,
            operators=operators
        )

        logger.info(f"[PRESIDIO] Anonymized {len(analysis_results)} PII entities into reversible tokens.")
        return anonymized_result.text, token_map


# Instantiate global anonymizer service
presidio_anonymizer_service = PresidioReversibleAnonymizer()
