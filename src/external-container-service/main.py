import os
import time
import torch
import requests
import openslide
from PIL import Image, ImageDraw
from techcyte_client import TechcyteClient


def gpu_test():
    """Run a simple GPU matrix multiplication test."""
    if not torch.cuda.is_available():
        print("CUDA is not available. No GPU detected.")
        return
    print(f"CUDA is available! Using GPU: {torch.cuda.get_device_name(0)}")
    size = 1000
    a = torch.randn(size, size, device="cuda")
    b = torch.randn(size, size, device="cuda")
    start_time = time.time()
    c = torch.matmul(a, b)
    end_time = time.time()
    print(
        f"Matrix multiplication ({size}x{size}) completed in {end_time - start_time:.4f} seconds"
    )
    print(f"Result sample: {c[0][0].item()}")


def download_image(url, save_path):
    """Download image from a URL to save_path."""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(save_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"Downloaded image to {save_path}")


def generate_fake_geojson(width, height, grid_size=2):
    """Generate fake GeoJSON with boxes in a grid_size x grid_size grid."""
    features = []
    box_width = width // grid_size
    box_height = height // grid_size
    for i in range(grid_size):
        for j in range(grid_size):
            x1 = i * box_width
            y1 = j * box_height
            x2 = x1 + box_width
            y2 = y1 + box_height
            bbox = [x1, y1, x2, y2]
            coordinates = [[[x1, y1], [x1, y2], [x2, y2], [x2, y1], [x1, y1]]]
            feature = {
                "type": "Feature",
                "bbox": bbox,
                "geometry": {"type": "Polygon", "coordinates": coordinates},
                "properties": {"annotation_type": "tissue_tumor_positive"},
            }
            features.append(feature)
    return {"type": "FeatureCollection", "features": features}


def process_image(image_path):
    """
    Customize this function with your image processing logic.
    Input: Path to SVS or TIFF file.
    Output: Dict with 'caseResults' and 'scanResults' per schema.
    Example: Places 4 boxes in a 2x2 grid on the highest resolution level.
    """
    slide = openslide.OpenSlide(image_path)
    width, height = slide.dimensions  # Highest resolution (level 0)
    geojson = generate_fake_geojson(width, height)
    num_boxes = len(geojson["features"])
    print(f"Generated {num_boxes} fake annotations.")
    return {
        "caseResults": {"mitosisCount": num_boxes},
        "scanResults": [
            {"scanId": os.environ.get("SCAN_ID", "test_scan"), "geojson": geojson}
        ],
    }


def main():
    gpu_test()

    required_envs = ["SCAN_URL", "HOST", "TASK_ID", "SCAN_ID"]
    for env in required_envs:
        if not os.environ.get(env):
            raise ValueError(f"Missing environment variable: {env}")
    image_path = "/tmp/downloaded_image.svs"
    download_image(os.environ["SCAN_URL"], image_path)
    print("Prod mode: Processing downloaded image")

    # Process image
    print(f"Processing image: {image_path}")
    results = process_image(image_path)

    print("Image processing complete. Posting to techcyte...")
    HOST = os.environ["HOST"]
    API_KEY_ID = os.environ.get("API_KEY_ID")
    API_KEY_SECRET = os.environ.get("API_KEY_SECRET")
    JWT_TOKEN = os.environ.get("JWT_TOKEN")

    client = TechcyteClient(
        host=HOST,
        jwt_token=JWT_TOKEN,
        api_key_id=API_KEY_ID,
        api_key_secret=API_KEY_SECRET,
    )
    try:
        response = client.post_results(os.environ["TASK_ID"], results)
        print(f"Success: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error posting results: {str(e)}")
        print(f"Results JSON (for debugging): {results}")


if __name__ == "__main__":
    main()
