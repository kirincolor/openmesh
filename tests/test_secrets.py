from openmesh.secrets import redact, write_env


def test_redact() -> None:
    assert redact("Bearer sk-secret-123 failed", "sk-secret-123") == "Bearer *** failed"


def test_write_env(tmp_path) -> None:
    write_env(tmp_path, {"OPENMESH_API_KEY": "sk-test", "OPENMESH_MODEL": "gpt-4o-mini"})
    text = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "OPENMESH_API_KEY=sk-test" in text
    write_env(tmp_path, {"OPENMESH_API_KEY": "sk-new"})
    text = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "sk-new" in text
    assert "sk-test" not in text
