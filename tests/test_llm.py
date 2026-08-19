from openmesh.llm import public_llm_error


def test_auth_errors_are_generic() -> None:
    assert public_llm_error(401, '{"error":{"code":"invalid_api_key"}}') == "Provider rejected the API key."
    assert "sk-" not in public_llm_error(401, "Bearer sk-test leaked")


def test_other_status_has_no_body() -> None:
    assert public_llm_error(500, "internal boom") == "LLM HTTP 500"
