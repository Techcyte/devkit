# Model Hosting Service: Docker Template

The **Model Hosting Service (MHS)** enables Techcyte users to run GPU-based batch processing by uploading custom Docker containers as classifiers. This repository provides a template for developing and testing your container locally or in a production-like environment.

We provide template files below that can be built upon and [deployed to the Techcyte infrastructure](guides/model-hosting-service/index.md).

Code Features:

- **Modularity**: Implement your image processing logic in `main.py`’s `process_image()` function.
- **Test locally**: Download an image from `SCAN_URL`, process it, and post results to Techcyte using provided environment variables.
- **GPU Support**: Uses NVIDIA CUDA with a simple GPU test via PyTorch.
- **Image Handling**: Supports DICOM/SVS/TIFF via `pydicom`, `openslide-python`

## Environment Variables

Production

  - `HOST`: Techcyte host (e.g., `ci.techcyte.com`).
  - `TASK_ID`: Task identifier.
  - `SCAN_ID`: Scan identifier.
  - `SCAN_URL`: Presigned S3 URL for image [`.svs`|`.tiff`|`.dcm`] download.
  - `SCAN_URL_ZIP`:  Presigned S3 URL for `.zip` download (DICOM only, for all layers).
  - `JWT_TOKEN`: A task specific jwt token used for authorizing requests to techcyte (not required for local testing)

Local testing

  - `API_KEY_ID`: Key id used while running locally
  - `API_KEY_SECRET`: Key secret used while running locally
  

## Step-by-step instructions

### 1. Clone the Repository:
   ```
   git clone https://github.com/Techcyte/devkit.git
   cd devkit/src/model-hosting-service
   ```

### 2. Customize Your Code
   - Edit `main.py`, replacing the `process_image()` function with your classifier logic.
   - Ensure the output matches the required schema (see below).
   - Add dependencies to `Dockerfile` if needed (e.g., `RUN pip3 install <package>`).

### 3. Build the Docker Image
  ```
  docker build -t my-docker-image:latest .
  ```

### 4. Test locally
   - Provide environment variables:
     ```
     docker run --rm --gpus all \
       -e HOST="ci.techcyte.com" \
       -e TASK_ID="your-task-id" \
       -e SCAN_ID="your-scan-id" \
       -e SCAN_URL="https://example.com/image.svs" \
       -e API_KEY_ID="your-api-key-id" \
       -e API_KEY_SECRET="your-api-key-secret" \
       my-docker-image:latest
     ```
   - If running on production `HOST="app.techcyte.com"`, CI `HOST="ci.techcyte.com"`
   - See [Creating a debug request](./guides/creating-a-debug-request/index.md) to obtain `TASK_ID`, `SCAN_ID` and `SCAN_URL` values
   - See [Creating an API key](./guides/creating-an-api-key/index.md) to obtain the api key id and secret
   - Downloads the image, processes it, and posts results to Techcyte. Prints results if posting fails.

### 5. Deploy
   - Push your image to the Techcyte container registry. See instructions [here](guides/model-hosting-service/index.md).


## Example Output (local output)
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
  - Ensure NVIDIA Docker is installed (`nvidia-model-toolkit`).
  - Verify `--gpus all` is used.
  - Check CUDA compatibility (image uses CUDA 11.8; ensure your GPU supports it).
  - If error persists, run without `--gpus all` to test CPU fallback.
- **Image Issues**: Ensure the input file is a valid SVS or TIFF. OpenSlide supports both.
- **Posting Errors**: Verify environment variables; invalid tokens print results for debugging.
- **Large Images**: OpenSlide handles large SVS files efficiently. For other formats (e.g., DICOM), add `pip3 install pydicom` to the Dockerfile.
- **Memory Issues**: Large images may require significant RAM; ensure your Docker host has enough resources.

## Posting Results

You will need to modify the `caseResults` and/or `scanResults` values to see your results on the Techcyte app. See [posting external model results](./guides/posting-external-model-results/index.md).
