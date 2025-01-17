import pytest
from pca_parser import FileHandler

def test_convert_pca_to_json():
    handler = FileHandler("/tmp/input", "/tmp/output", "/tmp/archive", {})
    pca_data = """[Section1]
key1=123
key2=test

[Section2]
key3=45.67
"""
    expected = {
        "Section1": {
            "key1": 123,
            "key2": "test"
        },
        "Section2": {
            "key3": 45.67
        }
    }
    result = handler.convert_pca_to_json(pca_data)
    assert result == expected 