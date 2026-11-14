import pytest
from mediflow.config import safe_path, runtime, APPROVED


def test_traversal(root):
    with pytest.raises(ValueError): safe_path(root, root/'..'/'escape')


def test_runtime_outside_approved():
    with pytest.raises(ValueError): runtime(APPROVED.parent/'other')


def test_contained_path(root):
    assert safe_path(root,root/'source'/'a.jsonl')==root/'source'/'a.jsonl'
