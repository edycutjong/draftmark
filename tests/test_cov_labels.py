from unittest.mock import Mock, patch
from PIL import Image

from api._core import labels, meta
from api._core.marks import MarkSystem, Token


def test_font_loading_error():
    """Test _font function for lines 26-30."""
    # Test the function with a normal size parameter
    with patch('PIL.ImageFont.load_default', return_value="test_font"):
        f = labels._font(22)
        assert f == "test_font"
    
    # Test the function when TypeError is raised (Pillow < 10.1 case)
    with patch('PIL.ImageFont.load_default', side_effect=[TypeError("test"), "fallback_font"]):
        f = labels._font(22)
        assert f == "fallback_font"


def test_schema_generation():
    """Test schema function for lines 47-54."""
    system = MarkSystem(scale=1.0)
    numbers = ["1", "2", "3"]
    
    schema = labels.schema(numbers, system)
    
    assert schema["type"] == "object"
    assert "properties" in schema
    assert schema["properties"]["1"]["type"] == "string"
    assert "?" in schema["properties"]["1"]["enum"]
    assert "1M" in schema["properties"]["1"]["enum"]
    assert len(numbers) == len(schema["required"])


def test_labels_annotate_basic():
    """Test annotate function for lines 33-44."""
    # Create a mock image
    img = Image.new('RGB', (100, 100), color='white')
    
    # Create mock tokens
    token1 = Token(track="track1", glyph_ids=(1,), box=(0.1, 0.1, 0.5, 0.5))
    token2 = Token(track="track2", glyph_ids=(2,), box=(0.6, 0.6, 0.9, 0.9))
    tokens = [token1, token2]
    
    annotated_img, numbering = labels.annotate(img, tokens)
    
    assert annotated_img.size == (100, 100)
    assert len(numbering) == 2
    assert "1" in numbering
    assert "2" in numbering
    assert numbering["1"] == "track1"
    assert numbering["2"] == "track2"


def test_labels_read():
    """Test read function for lines 57-73."""
    # Create a mock client
    mock_client = Mock(spec=meta.Client)
    
    # Create a mock image
    img = Image.new('RGB', (100, 100), color='white')
    
    # Create mock numbering
    numbering = {"1": "track1", "2": "track2"}
    
    # Create mock system
    system = MarkSystem(scale=1.0)
    
    # Mock the annotate function to return test data
    with patch.object(labels, 'annotate', return_value=(img, numbering)):
        # Mock the responses method to return a test response
        mock_response = {
            "id": "test-response-id",
            "output": [{"content": [{"type": "output_text", "text": '{"1": "12M", "2": "2"}'}]}]
        }
        mock_client.responses.return_value = mock_response
        
        by_track, details = labels.read(mock_client, img, numbering, system, feature="test")
        
        assert by_track == {"track1": "12M", "track2": "2"}
        assert details["response_id"] == "test-response-id"
        assert details["raw"] == {"1": "12M", "2": "2"}


def test_labels_read_with_hint():
    """Test read function with hint for line 65."""
    # Create a mock client
    mock_client = Mock(spec=meta.Client)
    
    # Create a mock image
    img = Image.new('RGB', (100, 100), color='white')
    
    # Create mock numbering
    numbering = {"1": "track1"}
    
    # Create mock system
    system = MarkSystem(scale=1.0)
    
    # Mock the annotate function to return test data
    with patch.object(labels, 'annotate', return_value=(img, numbering)):
        # Mock the responses method to return a test response with hint in prompt
        mock_response = {
            "id": "test-response-id",
            "output": [{"content": [{"type": "output_text", "text": '{"1": "12M"}'}]}]
        }
        mock_client.responses.return_value = mock_response
        
        hint = "previous reading failed"
        by_track, details = labels.read(mock_client, img, numbering, system, feature="test", hint=hint)
        
        assert by_track == {"track1": "12M"}
        assert details["response_id"] == "test-response-id"
        assert details["raw"] == {"1": "12M"}


def test_labels_read_image_processing():
    """Test image processing in read function for lines 59-61."""
    # Create a mock client
    mock_client = Mock(spec=meta.Client)
    
    # Create a mock image
    img = Image.new('RGB', (100, 100), color='white')
    
    # Create mock numbering
    numbering = {"1": "track1"}
    
    # Create mock system
    system = MarkSystem(scale=1.0)
    
    # Mock the annotate function
    with patch.object(labels, 'annotate', return_value=(img, numbering)):
        # Mock the bytes_data_url function
        with patch.object(meta, 'bytes_data_url') as mock_data_url:
            mock_data_url.return_value = "data:image/jpeg;base64,test"
            
            # Mock the responses method
            mock_response = {
                "id": "test-response-id",
                "output": [{"content": [{"type": "output_text", "text": '{"1": "12M"}'}]}]
            }
            mock_client.responses.return_value = mock_response
            
            by_track, details = labels.read(mock_client, img, numbering, system, feature="test")
            
            # Verify bytes_data_url was called
            mock_data_url.assert_called_once()
            assert by_track == {"track1": "12M"}
            assert details["response_id"] == "test-response-id"
            assert details["raw"] == {"1": "12M"}
