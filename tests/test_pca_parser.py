import pytest
import json
import os
from pca_parser import FileHandler

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

def test_nano_di_side_conversion():
    """Test conversion of real Nano Di Side PCA file"""
    # Initialize handler
    handler = FileHandler("/tmp/input", "/tmp/output", "/tmp/archive", {})
    
    # Load test data
    pca_data, expected_json = load_test_files()
    
    # Convert PCA to JSON
    result = handler.convert_pca_to_json(pca_data)
    
    # Test key parameters that must match exactly
    assert result['FDD'] == expected_json['FDD'], "FDD mismatch"
    assert result['FOD'] == expected_json['FOD'], "FOD mismatch"
    assert result['Magnification'] == expected_json['Magnification'], "Magnification mismatch"
    assert result['VoxelSizeX'] == expected_json['VoxelSizeX'], "VoxelSizeX mismatch"
    assert result['VoxelSizeY'] == expected_json['VoxelSizeY'], "VoxelSizeY mismatch"
    assert result['Voltage'] == expected_json['Voltage'], "Voltage mismatch"
    assert result['Current'] == expected_json['Current'], "Current mismatch"

def test_pca_section_parsing():
    """Test parsing of specific PCA sections"""
    handler = FileHandler("/tmp/input", "/tmp/output", "/tmp/archive", {})
    pca_data, _ = load_test_files()
    
    result = handler.convert_pca_to_json(pca_data)
    
    # Test Geometry section
    assert 'FDD' in result, "Missing FDD"
    assert isinstance(result['FDD'], float), "FDD should be float"
    
    # Test CT section
    assert 'NumberImages' in result, "Missing NumberImages"
    assert isinstance(result['NumberImages'], int), "NumberImages should be int"
    
    # Test Xray section
    assert 'Voltage' in result, "Missing Voltage"
    assert isinstance(result['Voltage'], int), "Voltage should be int"

def test_type_conversion():
    """Test proper type conversion of values"""
    handler = FileHandler("/tmp/input", "/tmp/output", "/tmp/archive", {})
    pca_data, _ = load_test_files()
    
    result = handler.convert_pca_to_json(pca_data)
    
    # Test numeric conversions
    assert isinstance(result['FDD'], float), "Float conversion failed"
    assert isinstance(result['NumberImages'], int), "Integer conversion failed"
    assert isinstance(result['Comment'], str), "String handling failed"

@pytest.mark.parametrize("test_input,expected", [
    ('FDD', 802.77534791),
    ('FOD', 105.8731875),
    ('Magnification', 7.58242353),
    ('Voltage', 190),
    ('Current', 130)
])
def test_specific_values(test_input, expected):
    """Test specific important values"""
    handler = FileHandler("/tmp/input", "/tmp/output", "/tmp/archive", {})
    pca_data, _ = load_test_files()
    
    result = handler.convert_pca_to_json(pca_data)
    assert result[test_input] == expected, f"{test_input} value mismatch" 