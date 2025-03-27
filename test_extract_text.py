from fastapi.testclient import TestClient
from PIL import Image
import io
import pytest
from main import app  # Replace with your actual application import

client = TestClient(app)

def create_test_image():
    # Create a simple black and white image for testing
    image = Image.new('RGB', (100, 30), color = (255, 255, 255))
    return image

def test_extract_text_from_images():
    # Create an in-memory image
    image = create_test_image()
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    # Simulate uploading the image
    files = {'files': [img_byte_arr,]}
    response = client.post("/extract-text/", files=files)

    assert response.status_code == 200
    assert 'extracted_texts' in response.json()
    assert len(response.json()['extracted_texts']) == 1
    assert response.json()['extracted_texts'][0]['filename'] == 'test_image.png'