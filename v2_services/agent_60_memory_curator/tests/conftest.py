import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture
def client(tmp_path):
    import main
    main.DOCS_ROOT = tmp_path
    (tmp_path / "projects" / "test_project" / "progress").mkdir(parents=True)
    (tmp_path / "sessions" / "cursor_reports").mkdir(parents=True)
    (tmp_path / "test.md").write_text("# Test\n\nHello world\n", encoding="utf-8")
    (tmp_path / "projects" / "test_project" / "progress" / "daily_log.md").write_text(
        "---\ncreated: 2026-04-25\n---\n\n# Daily Log\n\n## 2026-04-25\n\n- Test entry\n",
        encoding="utf-8"
    )
    return TestClient(main.app)
