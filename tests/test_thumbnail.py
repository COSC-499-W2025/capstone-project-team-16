import os
import sys
from unittest.mock import patch
from fastapi.testclient import TestClient

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from api import app, THUMBNAILS_DIR

client = TestClient(app)

def test_upload_thumbnail():
    """
    Verifies that the thumbnail upload endpoint:
    1. Accepts a file upload.
    2. Saves it to the correct directory with a safe filename.
    3. Updates the project customization.
    """
    project_id = "99:0"
    fake_image_content = b"fake_image_data"
    filename = "test_image.png"
    
    # Mock dependencies to avoid DB calls and validation logic
    with patch("api._get_project_by_id") as mock_get_proj, \
         patch("api.upsert_project_customization") as mock_upsert:
        
        mock_get_proj.return_value = {"project_id": project_id}
        # Mock the return of the DB update
        mock_upsert.return_value = {"thumbnail": "99_0_thumb.png"}

        response = client.post(
            f"/projects/{project_id}/thumbnail",
            files={"file": (filename, fake_image_content, "image/png")}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["thumbnail"] == "99_0_thumb.png"

        # Verify file existence on disk
        expected_filename = "99_0_thumb.png"
        expected_path = os.path.join(THUMBNAILS_DIR, expected_filename)
        
        assert os.path.exists(expected_path)
        
        # Clean up
        if os.path.exists(expected_path):
            os.remove(expected_path)
