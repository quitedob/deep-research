"""External checks are explicit so ordinary test runs never spend API credits."""
import os
import pytest


@pytest.fixture(autouse=True)
def require_live_opt_in():
    if os.getenv("RUN_LIVE_TESTS") != "1":
        pytest.skip("Set RUN_LIVE_TESTS=1 to call external providers")
