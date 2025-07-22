# External Container Service Docker Template

The **External Container Service (ECS)** enables Techcyte users to run GPU-based batch processing by uploading custom Docker containers as classifiers. This repository provides a template for developing and testing your container locally or in a production-like environment.

We provide template files below that can be built upon and [deployed to the Techcyte infrastructure](guides/external-container-service/index.md).

## Features
- **Modular Code**: Implement your image processing logic in `main.py`’s `process_image()` function.
- **Development Mode (`DEV=1`)**: Test locally with a mounted image, generate fake results (e.g., four boxes in a 2x2 grid), save a visualized output to `/output/result.png`, and print results.
- **Production Mode**: Download an image from `SCAN_URL`, process it, and post results to Techcyte using provided environment variables.
- **GPU Support**: Uses NVIDIA CUDA with a simple GPU test via PyTorch.
- **Image Handling**: Supports DICOM/SVS/TIFF via `pydicom`, `openslide-python`
- **Visualization**: In dev mode, draws red boxes on a downsampled image for result verification.

## Environment Variables
### Production (all required):
  - `SCAN_URL`: Presigned S3 URL for image download.
  - `HOST`: Techcyte host (e.g., `ci.techcyte.com`).
  - `JWT_TOKEN`: Token for Techcyte API.
  - `TASK_ID`: Task identifier.
  - `SCAN_ID`: Scan identifier.
### Development:
  - Only `DEV=1` is required; `SCAN_ID` defaults to `test_scan` if unset.

## Step-by-step instructions

### 1. Clone the Repository:
   ```
   git clone https://github.com/Techcyte/devkit.git
   cd devkit/src/external-container-service
   ```

### 2. Customize Your Code
   - Edit `main.py`, replacing the `process_image()` function with your classifier logic.
   - Ensure the output matches the required schema (see below).
   - Add dependencies to `Dockerfile` if needed (e.g., `RUN pip3 install <package>`).

### 3. Build the Docker Image
  ```
  docker build -t my-docker-image:latest .
  ```

### 4. Test in Development Mode
   - Prepare input and output directories:
     ```
     mkdir -p input output
     cp /path/to/your/image.svs input/image.svs
     # OR
     curl https://openslide.cs.cmu.edu/download/openslide-testdata/Aperio/CMU-1.svs -o input/image.svs
     ```
   - Run with GPU support:
     ```
      docker run --rm --gpus all \
      -e DEV=1 -e SCAN_ID="test_scan" \
      -v $(pwd)/input:/input \
      -v $(pwd)/output:/output \
      -v $(pwd)/main.py:/app/main.py \
      -v $(pwd)/techcyte_client.py:/app/techcyte_client.py \
      my-docker-image:latest
     ```
   - **Output**:
     - Console: GPU test results and JSON output.
     - File: `/output/result.png` (downsampled image with red boxes).

### 5. Test in Production Mode (not typical)
   - Provide environment variables:
     ```
     docker run --rm --gpus all \
       -e SCAN_URL="https://example.com/image.svs" \
       -e HOST="ci.techcyte.com" \
       -e JWT_TOKEN="your-token" \
       -e TASK_ID="your-task-id" \
       -e SCAN_ID="your-scan-id" \
       my-docker-image:latest
     ```
   - Downloads the image, processes it, and posts results to Techcyte. Prints results if posting fails.

### 6. Deploy
   - Push your image to the Techcyte external container registry. See instructions [here](guides/external-container-service/index.md).

## Results Schema

```json
{
  "caseResults": {
    "mitosisCount": 4
  },
  "scanResults": [
    {
      "scanId": "8615687",
      "geojson": {
        "type": "FeatureCollection",
        "features": [
          {
            "type": "Feature",
            "bbox": [x1, y1, x2, y2],
            "geometry": {
              "type": "Polygon",
              "coordinates": [[[x1,y1], [x1,y2], [x2,y2], [x2,y1], [x1,y1]]]
            },
            "properties": {
              "annotation_type": "tissue_tumor_positive"
            }
          }
        ]
      }
    }
  ]
}
```

See [Techcyte Swagger Docs](https://api.app.techcyte.com/docs/#/External%20Results/ExternalResults) for more details on posting results.

## Example Output (Dev Mode)
```
CUDA is available! Using GPU: Tesla T4
Matrix multiplication (1000x1000) completed in 0.0246 seconds
Result sample: 21.861495971679688
Processing image: /input/image.svs
Generated 4 fake annotations
Visualization saved to /output/result.png
Results JSON: {"caseResults": {"mitosisCount": 4}, "scanResults": [{"scanId": "test_scan", "geojson": {...}}]}
```

You should have an image with a 2x2 grid or red squares.


## Troubleshooting
- **No GPU**:
  - Ensure NVIDIA Docker is installed (`nvidia-container-toolkit`).
  - Verify `--gpus all` is used.
  - Check CUDA compatibility (image uses CUDA 11.8; ensure your GPU supports it).
  - If error persists, run without `--gpus all` to test CPU fallback.
- **Image Issues**: Ensure the input file is a valid SVS or TIFF. OpenSlide supports both.
- **Posting Errors**: Verify environment variables; invalid tokens print results for debugging.
- **Large Images**: OpenSlide handles large SVS files efficiently. For other formats (e.g., DICOM), add `pip3 install pydicom` to the Dockerfile.
- **Memory Issues**: Large images may require significant RAM; ensure your Docker host has enough resources.