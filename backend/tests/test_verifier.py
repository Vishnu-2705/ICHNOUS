"""
Unit tests for Closed-Loop Patch Verifier module.
"""

import sys
from pathlib import Path
import pytest

# Ensure sys.path includes backend and project root
backend_dir = Path(__file__).resolve().parent.parent
project_dir = backend_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

from agent365.engine.verifier import verify_patch


class TestPatchVerifier:
    def test_verify_patch_success(self):
        code = "def search(): return 'stale policy 2023'"
        diff = "--- a/prompts/filter.txt\n+++ b/prompts/filter.txt\n@@ -1,3 +1,4 @@\n+search(filter={'effective_year': 2025})"

        result = verify_patch(code, diff)
        assert result["verified"] is True
        assert result["verification_status"] == "verified_pass"
        assert result["confidence_boost"] == 0.15

    def test_verify_patch_empty_diff(self):
        result = verify_patch("code", "")
        assert result["verified"] is False
        assert result["verification_status"] == "unverified_no_diff"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
