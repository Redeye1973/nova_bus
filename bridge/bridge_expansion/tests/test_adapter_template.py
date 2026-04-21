"""Generic adapter test template. Cursor past TOOL_NAME aan per adapter.

Usage: pytest tests/adapters/test_<tool>_adapter.py
"""
import pytest
from fastapi.testclient import TestClient

# Cursor: import main app
# from app.main import app

# client = TestClient(app)

TOOL_NAME = "blender"  # Cursor past aan


class TestStatusEndpoint:
    """Test status endpoint van adapter."""
    
    def test_status_returns_200(self, client):
        response = client.get(f"/{TOOL_NAME}/status")
        assert response.status_code == 200
    
    def test_status_has_required_fields(self, client):
        response = client.get(f"/{TOOL_NAME}/status")
        data = response.json()
        assert "tool" in data
        assert "available" in data
        assert data["tool"] == TOOL_NAME
    
    def test_status_reports_version_if_available(self, client):
        response = client.get(f"/{TOOL_NAME}/status")
        data = response.json()
        if data["available"]:
            assert "version" in data
            assert data["version"] is not None


class TestErrorHandling:
    """Test graceful errors."""
    
    def test_invalid_input_returns_400_or_422(self, client):
        # Tool-specific: Cursor past payload aan
        response = client.post(f"/{TOOL_NAME}/some_operation", json={"invalid": "data"})
        assert response.status_code in (400, 422, 404, 500)
    
    def test_missing_file_returns_404(self, client):
        response = client.post(
            f"/{TOOL_NAME}/example_op",
            json={"input_path": "/nonexistent/file.xyz", "output_path": "/tmp/out.xyz"}
        )
        # 404 of 422 (pydantic validation) acceptabel
        assert response.status_code in (404, 422)


class TestBasicOperations:
    """Happy path tests per adapter. Cursor implementeert per tool."""
    
    @pytest.mark.skip(reason="Cursor: implementeer basic happy path test")
    def test_basic_operation_success(self, client, tmp_path):
        # Voorbeeld pattern:
        # 1. Bereid test fixture voor (sample file in tmp_path)
        # 2. Call endpoint met valid params
        # 3. Assert 200 response
        # 4. Assert output file created
        pass


# === FIXTURES ===

@pytest.fixture
def sample_png(tmp_path):
    """Create sample PNG voor tests."""
    from PIL import Image
    img = Image.new("RGB", (64, 64), color="red")
    path = tmp_path / "sample.png"
    img.save(path)
    return str(path)


@pytest.fixture
def sample_svg(tmp_path):
    """Create sample SVG voor tests."""
    svg_content = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect width="64" height="64" fill="blue"/></svg>'
    path = tmp_path / "sample.svg"
    path.write_text(svg_content)
    return str(path)


@pytest.fixture
def minimal_godot_project(tmp_path):
    """Create minimale Godot project structuur voor tests."""
    project_file = tmp_path / "project.godot"
    project_file.write_text("""; Engine configuration
config_version=5

[application]
config/name="Test Project"
config/features=PackedStringArray("4.3", "Forward Plus")
""")
    return str(tmp_path)
