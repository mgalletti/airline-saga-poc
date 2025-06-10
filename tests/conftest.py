"""Configure pytest for the project."""

import pytest

# This registers the asyncio marker with pytest
pytest.importorskip("pytest_asyncio")