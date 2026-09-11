from pathlib import Path
import pytest
from backend.services.interaction_service import describe_image


@pytest.mark.live
async def test_default_deepseek_vlm_describes_tracked_fixture():
    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "research-sample.jpg"
    assert fixture.is_file(), "The tracked image fixture is required"
    assert (await describe_image(fixture.read_bytes())).strip()
