from pathlib import Path
import uuid
import pytest
from mediflow.config import APPROVED, runtime
from mediflow.generate import generate, write_batch


@pytest.fixture
def root():
    return runtime(APPROVED / "tests" / str(uuid.uuid4()))


@pytest.fixture
def rows():
    return generate(patients=10, appointments=30)


@pytest.fixture
def batch(root, rows):
    return write_batch(root, "baseline", rows)
