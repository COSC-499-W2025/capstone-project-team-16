import zipfile
from pathlib import Path


ROOT = Path("input/test-data")


def _names(zip_path: Path):
    with zipfile.ZipFile(zip_path) as zf:
        return set(zf.namelist())


def test_incremental_snapshot_zip_fixtures_exist_and_have_required_structure():
    earlier = ROOT / "code_collab_proj_snapshot_earlier.zip"
    later = ROOT / "code_collab_proj_snapshot_later.zip"

    assert earlier.exists()
    assert later.exists()

    earlier_names = _names(earlier)
    later_names = _names(later)

    assert any(name.startswith("code_collab_proj/app/") for name in earlier_names)
    assert any(name.startswith("code_collab_proj/test/") for name in earlier_names)
    assert any(name.startswith("code_collab_proj/doc/") for name in earlier_names)

    assert any(name.startswith("code_collab_proj/app/") for name in later_names)
    assert any(name.startswith("code_collab_proj/test/") for name in later_names)
    assert any(name.startswith("code_collab_proj/doc/") for name in later_names)

    # Later snapshot should contain additional files to simulate incremental info.
    assert len(later_names) > len(earlier_names)


def test_multi_project_zip_fixture_contains_code_text_and_image_projects():
    multi = ROOT / "multi_project_test_data.zip"
    assert multi.exists()

    names = _names(multi)
    assert any(name.startswith("code_indiv_proj/") for name in names)
    assert any(name.startswith("code_collab_proj/") for name in names)
    assert any(name.startswith("text_indiv_proj/") for name in names)
    assert any(name.startswith("image_indiv_proj/") for name in names)
