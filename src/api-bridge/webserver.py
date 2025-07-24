import argparse
import os
import json
import aiohttp
import aiofiles
from fastapi import FastAPI, Request, HTTPException
from concurrent.futures import ThreadPoolExecutor
import uvicorn
import openslide
import logging
from urllib.parse import urlparse
import asyncio

from techcyte_client import TechcyteClient

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()
executor = ThreadPoolExecutor(max_workers=4)  # Adjust based on CPU cores

CACHE_DIR = "cache"
TECHCYTE_HOST = "ci.techcyte.com"  # OR 'app.techcyte.com' for production


async def download_image(url, save_path):
    """Download image asynchronously from a URL to save_path."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            async with aiofiles.open(save_path, "wb") as f:
                async for chunk in response.content.iter_chunked(8192):
                    await f.write(chunk)
    logger.info(f"Downloaded image to {save_path}")


def process_image(image_path, data):
    """Process image and generate results."""
    slide = None
    try:
        scans = data.get("scans", {})
        if not scans:
            raise ValueError("No scans provided in data")
        scan_id, _ = next(iter(scans.items()))  # First scan
        slide = openslide.OpenSlide(image_path)
        width, height = slide.dimensions
        geojson = generate_fake_geojson(width, height)
        num_boxes = len(geojson["features"])
        logger.info(f"Generated {num_boxes} fake annotations for {image_path}")
        logger.debug(f"GeoJSON: {json.dumps(geojson, indent=2)}")
        return {
            "caseResults": {"mitosisCount": num_boxes},
            "scanResults": [{"scanId": scan_id, "geojson": geojson}],
        }
    finally:
        if slide:
            slide.close()  # Ensure slide is closed to free resources


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


async def background_task_handler(data):
    """Handle background processing of webhook data."""
    try:
        scans = data.get("scans", {})
        if not scans:
            raise ValueError("No scans provided in data")
        scan_id, scan_url = next(iter(scans.items()))

        os.makedirs(CACHE_DIR, exist_ok=True)
        # Extract file extension from URL
        parsed_url = urlparse(scan_url)
        file_ext = os.path.splitext(parsed_url.path)[1] or ".svs"
        image_path = os.path.join(CACHE_DIR, f"image{file_ext}")

        logger.info(f"Starting download for {scan_url}")
        await download_image(scan_url, image_path)

        logger.info(f"Processing image {image_path}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(executor, process_image, image_path, data)

        api_key_id = os.environ.get("API_KEY_ID")
        api_key_secret = os.environ.get("API_KEY_SECRET")
        # jwt is necessary for production environments, not required for local testing
        jwt_token = data.get("jwt_token")

        if not api_key_id or not api_key_secret:
            raise ValueError("API key ID or secret not provided")

        client = TechcyteClient(
            host=TECHCYTE_HOST,
            jwt_token=jwt_token,
            api_key_id=api_key_id,
            api_key_secret=api_key_secret,
        )
        logger.info(f"Posting results for task {data.get('task_id')}")
        client.post_results(data.get("task_id"), result)

        return {"statusCode": 200, "body": json.dumps(result)}
    except Exception as e:
        logger.error(f"Error in background processing: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": f"Error in background processing: {str(e)}"}
            ),
        }


@app.post("/webhook")
async def webhook(request: Request):
    """Handle POST webhook requests."""
    try:
        data = await request.json()
        logger.info(f"Received webhook data: {data}")

        # Start background task and return immediately
        loop = asyncio.get_running_loop()
        loop.create_task(background_task_handler(data))
        return {"message": "Processing started"}
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="FastAPI app for image processing with Techcyte API"
    )
    parser.add_argument("--port", type=int, default=3000, help="Port to run the app")
    parser.add_argument("--image-path", type=str, help="Custom path to image file")
    parser.add_argument(
        "--api-key-secret", type=str, required=True, help="API key secret"
    )
    parser.add_argument("--api-key-id", type=str, required=True, help="API key ID")
    args = parser.parse_args()

    # Set environment variables for worker processes
    os.environ["API_KEY_ID"] = args.api_key_id
    os.environ["API_KEY_SECRET"] = args.api_key_secret
    # Optional: os.environ['IMAGE_PATH'] = args.image_path or ''

    logger.info(f"Initialized API_KEY_ID: {args.api_key_id}")
    logger.info(f"Initialized API_KEY_SECRET: {args.api_key_secret}")

    # Run Uvicorn with correct import string (file is named webserver.py)
    uvicorn.run("webserver:app", host="0.0.0.0", port=args.port, workers=2)
