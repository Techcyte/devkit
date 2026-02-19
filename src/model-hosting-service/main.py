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


def generate_fake_geojson(width, height):
    """
    Generates a fake GeoJSON with 4 boxes in a 2x2 grid.
    """
    box_size = min(width, height) // 8  # Smaller boxes for demonstration
    features = []
    for i in range(2):
        for j in range(2):
            x_center = (width // 4) * (2 * i + 1)
            y_center = (height // 4) * (2 * j + 1)
            poly = [
                [x_center - box_size // 2, y_center - box_size // 2],
                [x_center - box_size // 2, y_center + box_size // 2],
                [x_center + box_size // 2, y_center + box_size // 2],
                [x_center + box_size // 2, y_center - box_size // 2],
                [
                    x_center - box_size // 2,
                    y_center - box_size // 2,
                ],  # Close the polygon
            ]
            feature = {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [poly]},
                "properties": {"name": "Mitosis", "color": "#ff0000"},
            }
            features.append(feature)
    return {"type": "FeatureCollection", "features": features}


def process_image(image_path):
    """
    Customize this function with your image processing logic.
    Input: Path to SVS or TIFF file.
    Output: Dict with AI workflow structure including dummy key-value pairs.
    Example: Places 4 boxes in a 2x2 grid on the highest resolution level.
    """
    slide = openslide.OpenSlide(image_path)
    width, height = slide.dimensions  # Highest resolution (level 0)
    geojson = generate_fake_geojson(width, height)
    num_boxes = len(geojson["features"])
    print(f"Generated {num_boxes} fake annotations.")

    # Dummy mitosis count based on number of boxes
    mitosis_count = num_boxes
    # Dummy diagnosis
    diagnosis = "Benign"
    # Dummy score
    dummy_score = f"{mitosis_count}+"
    # Dummy tumor percentage
    tumor_percentage = f"Percentage: {mitosis_count * 0.2:.2f}%"

    return {
        "model_name": "Mitosis Detection Model",
        "provider": "Acme AI",
        "ruo": True,  # Indicates Research Use Only
        "report": {
            "type": "Basic",
            "results": [
                {"name": "Result", "result": diagnosis},
                {"name": "Mitosis Count", "result": str(mitosis_count)},
                {"name": "Dummy Score", "result": dummy_score},
            ],
            "segments": [
                {
                    "name": "Tumor",
                    "result": tumor_percentage,
                    "feature_collection": {"type": "FeatureCollection", "features": []},
                },
                {"name": "Mitosis", "result": "", "feature_collection": geojson},
            ],
        },
    }


def main():
    # gpu_test()

    required_envs = ["SCAN_URL", "HOST", "TASK_ID", "SCAN_ID"]
    for env in required_envs:
        if not os.environ.get(env):
            raise ValueError(f"Missing environment variable: {env}")
    image_path = "/tmp/downloaded_image.svs"
    download_image(os.environ["SCAN_URL"], image_path)
    print("Prod mode: Processing downloaded image")

    # Process image
    print(f"Processing image: {image_path}")
    workflow_results = process_image(image_path)

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
        scan_id = os.environ["SCAN_ID"]
        full_json = {
            "caseResults": {},
            "scanResults": [{"scanId": scan_id, "workflow": workflow_results}],
        }
        response = client.post_results(os.environ["TASK_ID"], full_json)
        print(f"Success: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error posting results: {str(e)}")
        print(f"Results JSON (for debugging): {full_json}")


if __name__ == "__main__":
    main()
