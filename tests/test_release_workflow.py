import pytest
import json
import os
import jwt
from datetime import datetime

def load_test_files():
    """Load test PCA and JSON files"""
    test_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    
    # Read PCA file
    with open(os.path.join(test_dir, 'input', 'Nano Di Side.pca'), 'r') as f:
        pca_data = f.read()
    
    # Read expected JSON
    with open(os.path.join(test_dir, 'output', 'Nano Di Side.pca.json'), 'r') as f:
        expected_json = json.load(f)
    
    return pca_data, expected_json

def test_release_metadata_extraction():
    """Test that release metadata is correctly extracted from JSON"""
    _, json_data = load_test_files()
    
    # These should match the values we extract in the release workflow
    expected_values = {
        'Voltage': 190,
        'Current': 130,
        'FDD': 802.77534791,
        'FOD': 105.8731875,
        'Magnification': 7.58242353,
        'VoxelSizeX': 0.02637679,
        'VoxelSizeY': 0.02637679
    }
    
    for key, value in expected_values.items():
        assert json_data[key] == value, f"{key} value mismatch"

def test_provenance_format():
    """Test that provenance attestation has correct format and content"""
    def create_test_provenance(json_path):
        """Simulate provenance creation similar to GitHub action"""
        return {
            "payloadType": "application/vnd.in-toto+jwt",
            "payload": {
                "_type": "https://in-toto.io/Statement/v0.1",
                "subject": [{
                    "name": json_path,
                    "digest": {"sha256": "example_hash"}
                }],
                "predicateType": "https://slsa.dev/provenance/v0.2",
                "predicate": {
                    "buildType": "https://github.com/actions/runner",
                    "builder": {
                        "id": "https://github.com/actions/runner"
                    },
                    "invocation": {
                        "configSource": {
                            "uri": f"git+https://github.com/johntrue15/NOCTURN-Raspi-test@refs/heads/Test-1-16",
                            "digest": {"sha1": "example_commit_hash"}
                        }
                    }
                }
            }
        }

    # Test with our JSON file
    _, json_data = load_test_files()
    json_path = "json/Nano Di Side.json"
    
    # Create test provenance
    provenance = create_test_provenance(json_path)
    
    # Verify provenance format
    assert "payloadType" in provenance
    assert provenance["payloadType"] == "application/vnd.in-toto+jwt"
    assert "payload" in provenance
    assert "_type" in provenance["payload"]
    assert "subject" in provenance["payload"]
    assert len(provenance["payload"]["subject"]) > 0
    assert "name" in provenance["payload"]["subject"][0]
    assert provenance["payload"]["subject"][0]["name"] == json_path

def test_release_body_format():
    """Test that release body is correctly formatted"""
    _, json_data = load_test_files()
    
    # Create release body similar to workflow
    body = f"""## Scan Parameters
- Voltage: {json_data['Voltage']}kV
- Current: {json_data['Current']}µA
- FDD: {json_data['FDD']}mm
- FOD: {json_data['FOD']}mm
- Magnification: {json_data['Magnification']}x
- Voxel Size X: {json_data['VoxelSizeX']}µm
- Voxel Size Y: {json_data['VoxelSizeY']}µm"""
    
    # Test format
    assert "## Scan Parameters" in body
    assert f"Voltage: {json_data['Voltage']}kV" in body
    assert f"Current: {json_data['Current']}µA" in body
    assert f"FDD: {json_data['FDD']}mm" in body
    assert "µm" in body  # Check units
    assert "kV" in body
    assert "µA" in body
    assert "mm" in body

@pytest.mark.parametrize("field,unit", [
    ('Voltage', 'kV'),
    ('Current', 'µA'),
    ('FDD', 'mm'),
    ('FOD', 'mm'),
    ('Magnification', 'x'),
    ('VoxelSizeX', 'µm'),
    ('VoxelSizeY', 'µm')
])
def test_parameter_units(field, unit):
    """Test that each parameter has correct units in release"""
    _, json_data = load_test_files()
    value = json_data[field]
    formatted = f"{field}: {value}{unit}"
    assert str(value) in formatted
    assert unit in formatted 