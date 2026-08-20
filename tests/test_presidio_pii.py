import pytest
from presidio_governance.anonymizer import presidio_anonymizer_service
from presidio_governance.rehydrator import presidio_rehydrator_service


def test_presidio_anonymize_and_map():
    sample_text = "Issue reported by EMP-998877 at admin@corp.com on IP 10.0.0.12"
    anonymized, token_map = presidio_anonymizer_service.anonymize_and_map(sample_text)

    assert "admin@corp.com" not in anonymized
    assert "EMP-998877" not in anonymized
    assert "<ANON_EMAIL_ADDRESS_" in anonymized
    assert "<ANON_ENTERPRISE_EMP_ID_" in anonymized
    assert len(token_map) >= 2


def test_presidio_rehydration():
    token_map = {
        "<ANON_PERSON_112233>": "John Doe",
        "<ANON_IP_ADDRESS_445566>": "192.168.1.100"
    }
    anonymized_solution = "Restarting instance for <ANON_PERSON_112233> at <ANON_IP_ADDRESS_445566>."
    rehydrated = presidio_rehydrator_service.rehydrate_text(anonymized_solution, token_map)

    assert "John Doe" in rehydrated
    assert "192.168.1.100" in rehydrated
    assert "<ANON_PERSON_112233>" not in rehydrated

