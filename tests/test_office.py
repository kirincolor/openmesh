from pathlib import Path

from openmesh.config import AgentConfig, MeshConfig, MeshMeta, ProviderConfig
from openmesh.office import infer_kind, write_office
from openmesh.runtime import Mesh
from openmesh.vault import Vault


def test_infer_kind() -> None:
    assert infer_kind("plan.docx") == "docx"
    assert infer_kind("sheet", "excel") == "xlsx"
    assert infer_kind("talk", "slides") == "pptx"


def test_office_files_land_on_disk(tmp_path: Path) -> None:
    config = MeshConfig(
        root=tmp_path,
        mesh=MeshMeta(chief="coder"),
        provider=ProviderConfig(api_key="x"),
        agents=[
            AgentConfig(
                id="coder",
                name="Coder",
                role="code",
                tools=["office_write", "pc_write", "pc_list"],
            )
        ],
    )
    mesh = Mesh(config)
    agent = config.agent("coder")
    word = mesh.tools.run(
        agent,
        "office_write",
        {"path": "reports/brief.docx", "title": "Brief", "body": "Hello\n\n- one\n- two"},
    )
    assert word.startswith("LOCAL::")
    assert (tmp_path / "computer" / "reports" / "brief.docx").is_file()
    sheet = mesh.tools.run(
        agent,
        "office_write",
        {"path": "reports/data.xlsx", "rows": [["a", "b"], ["1", "2"]]},
    )
    assert sheet.startswith("LOCAL::")
    assert (tmp_path / "computer" / "reports" / "data.xlsx").is_file()
    deck = mesh.tools.run(
        agent,
        "office_write",
        {"path": "reports/talk.pptx", "slides": [{"title": "Hi", "body": "There"}]},
    )
    assert deck.startswith("LOCAL::")
    assert (tmp_path / "computer" / "reports" / "talk.pptx").is_file()


def test_write_office_helper(tmp_path: Path) -> None:
    path = tmp_path / "n.docx"
    write_office(path, "docx", title="N", body="text")
    assert path.is_file()
    assert path.stat().st_size > 100


def test_office_granted_with_pc_write(tmp_path: Path) -> None:
    config = MeshConfig(
        root=tmp_path,
        mesh=MeshMeta(),
        provider=ProviderConfig(api_key="x"),
        agents=[AgentConfig(id="coder", name="Coder", role="code", tools=["pc_write"])],
    )
    vault = Vault(config)
    assert "office_write" in vault.allowed(config.agent("coder"))
