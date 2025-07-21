import argparse
import os
import json
import requests
from flask import Flask, request, jsonify
import asyncio
import openslide
from PIL import ImageDraw
import aiofiles
from concurrent.futures import ThreadPoolExecutor
import uvicorn
from asgiref.wsgi import WsgiToAsgi

from techcyte_client import TechcyteClient

app = Flask(__name__)
executor = ThreadPoolExecutor()

# Default image URL and cache path
DEFAULT_IMAGE_URL = (
    "https://openslide.cs.cmu.edu/download/openslide-testdata/Aperio/CMU-1.svs"
)
CACHE_DIR = "cache"
DEFAULT_IMAGE_PATH = os.path.join(CACHE_DIR, "image.svs")

TECHCYTE_HOST = "app.techcyte.com"  # OR 'ci.techcyte.com' for CI testing


def download_image(url, save_path):
    """Download image from a URL to save_path."""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(save_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"Downloaded image to {save_path}")


def process_image(image_path, data):
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
    print("GeoJSON:", json.dumps(geojson, indent=2))
    return {
        "caseResults": {"mitosisCount": num_boxes},
        "scanResults": [{"scanId": data.get("scan_id"), "geojson": geojson}],
    }


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


def visualize_boxes(slide, geojson, output_path, downsample_factor=100):
    """Draw GeoJSON boxes on a downsampled image and save to output_path."""
    level = slide.get_best_level_for_downsample(downsample_factor)
    downsampled = slide.read_region((0, 0), level, slide.level_dimensions[level])
    draw = ImageDraw.Draw(downsampled)
    level_downsample = slide.level_downsamples[level]
    for feature in geojson["features"]:
        bbox = feature["bbox"]
        scaled_bbox = [coord / level_downsample for coord in bbox]
        draw.rectangle(scaled_bbox, outline="red", width=2)
    downsampled.save(output_path)
    print(f"Visualization saved to {output_path}")


async def background_task_handler(data):
    """Handle background processing of webhook data."""
    try:
        image_path = args.image_path or DEFAULT_IMAGE_PATH
        # Ensure cache directory exists
        if not args.image_path and not os.path.exists(image_path):
            os.makedirs(CACHE_DIR, exist_ok=True)
            download_image(DEFAULT_IMAGE_URL, image_path)

        # Process image
        result = await asyncio.get_event_loop().run_in_executor(
            executor, process_image, image_path, data
        )

        # Visualize if in local_dev mode
        if data.get("local_dev"):
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, "output.png")
            slide = openslide.OpenSlide(image_path)
            await asyncio.get_event_loop().run_in_executor(
                executor,
                visualize_boxes,
                slide,
                result["scanResults"][0]["geojson"],
                output_path,
            )
        else:
            client = TechcyteClient(
                host=TECHCYTE_HOST,
                api_key_id=args.get("api_key_id"),
                api_key_secret=args.get("api_key_secret"),
            )
            try:
                response = client.post_results(data.get("task_id"), result)
                print(f"Success: {response.status_code}")
            except requests.RequestException as e:
                print(f"Error posting results: {str(e)}")
                print(f"Results JSON (for debugging): {result}")

        return {"statusCode": 200, "body": json.dumps(result)}
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": f"Error in background processing: {str(e)}"}
            ),
        }


@app.route("/webhook", methods=["POST"])
async def webhook():
    """Handle POST webhook requests."""
    data = request.get_json() or {}
    print(f"Received webhook data: {data}")

    # Start background task and return immediately
    asyncio.create_task(background_task_handler(data))
    return jsonify({"message": "Processing started"}), 200


@app.route("/image", methods=["GET"])
async def image():
    """Serve a mocked image file."""
    image_path = args.image_path or DEFAULT_IMAGE_PATH

    # If no custom path and image doesn't exist, download it
    if not args.image_path and not os.path.exists(image_path):
        os.makedirs(CACHE_DIR, exist_ok=True)
        await asyncio.get_event_loop().run_in_executor(
            executor, download_image, DEFAULT_IMAGE_URL, image_path
        )

    if not os.path.exists(image_path):
        return jsonify({"message": "Image not found"}), 404

    async with aiofiles.open(image_path, "rb") as f:
        content = await f.read()

    return app.response_class(response=content, status=200, mimetype="image/svs")


if __name__ == "__main__":
    # Command-line arguments
    parser = argparse.ArgumentParser(
        description="Flask app for image processing with Techcyte API bridge"
    )
    parser.add_argument(
        "--port", type=int, default=3000, help="Port to run the Flask app"
    )
    parser.add_argument("--image-path", type=str, help="Custom path to image file")
    parser.add_argument(
        "--api-key-secret", type=str, help="API key secret for Techcyte client"
    )
    parser.add_argument("--api-key-id", type=str, help="API key ID for Techcyte client")
    args = parser.parse_args()

    asgi_app = WsgiToAsgi(app)  # Wrap Flask app for ASGI compatibility
    uvicorn.run(asgi_app, host="0.0.0.0", port=args.port)
