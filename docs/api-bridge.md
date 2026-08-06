# Building an API Bridge

Using Techcyte's classification webhook system, third-party developers can run their image classification code on their own infrastructure and report results back to Techcyte. When a user creates an image classification task, the webhook is notified with the appropriate variables listed [below](#webhook-variables).

Example Code Features:

- **Modular Code**: Implement your image processing logic in `webserver.py`’s `process_image()` function.
- **Image Handling**: Support DICOM/SVS/TIFF via `pydicom`, `openslide-python`
- **Visualization**: On the Techcyte app, four box objects are drawn on the image for result verification.

## Webhook variables

**Supplied in Production**:

  - `company_id`: Company identifier, useful for billing
  - `scans`: A mapping of scan identifiers to presigned image download url
  - `scan_urls`: A mapping of scan identifiers to **every** presigned download url for that scan. A DICOM series is stored as many objects, so it yields one url per file; `SVS`/`TIFF` scans (and unprocessed single-file DICOM) yield a single url. `scans` holds only the first url of each list, so prefer `scan_urls` if you handle DICOM series or similar and need more than just the base layer.
  - `stains`: A mapping of scan identifiers to that scan's stain metadata. Scans with no recorded stain are left out of the map, so it may be empty or absent entirely. Each entry has:
      - `value`: The stain recorded on the scan, as free-form text. The slide's stain wins over the scan's own stain when both are set.
      - `stain_code`: The matching stain code configured for your company. Omitted when `value` does not match a configured stain.
      - `label`: The display label of that configured stain. Omitted alongside `stain_code`.
  - `task_id`: Task identifier
  - `case_id`: The assigned case id (unused for most calls)
  - `model_id`: A user supplied variable used to customize webhook calls
  - `jwt_token`: A task specific jwt token used for authorizing requests to techcyte (not required for local testing)


## Getting Started

### 1. Clone the Repository:
   ```
   git clone https://github.com/Techcyte/devkit.git
   cd devkit/src/api-bridge
   ```

### 2. Run the example:

- You'll need to generate an API key and specify when running the webserver. See [creating an API key](./guides/creating-an-api-key/index.md)
- Start the webserver
```
# Install requirements with
# pip install -r requirements.txt
# openslide-bin may be required depending on your system
# pip install openslide-bin
python webserver.py --port 3000 --api-key-id e-_tfr-redacted-Vhjt --api-key-secret FNI-redacted-LvH
```

- Mock a techcyte webhook request. See [creating a debug request](guides/creating-a-debug-request/index.md) for test `data` variables.
```
 curl -X POST --url "http://localhost:3000/webhook" \
 --header "Content-Type: application/json" \
 --data '{ \
    "company_id": "2380941", \
    "scans": { \
      "8823846": "https://techcyteci-preprod.s3.us-west-2.amazonaws.com/redacted" \
    }, \
    "scan_urls": { \
      "8823846": ["https://techcyteci-preprod.s3.us-west-2.amazonaws.com/redacted"] \
    }, \
    "stains": { \
      "8823846": { "value": "HE", "stain_code": "HE", "label": "H&E" } \
    }, \
    "case_id": "aHVtYW5DYXNlOjI0MjEzNjY=", \
    "task_id": "dGFzazoxODU4MzU=", \
    "model_name": "" \
  }'
```

### 3. Customize Your Code:
   - Edit `webserver.py`, replacing the `process_image()` function with your classifier logic.
   - Ensure the output matches the required schema (see below).


It is possible to run this example with `ngrok` (https://ngrok.com) and process Techcyte images locally for testing (`ngrok http 3000`). But a more robust solution should be implemented for production environments.

### 4. Deploying

See [creating a debug request](guides/creating-a-debug-request/index.md) for setting up your endpoint in the Techcyte app. The only difference is you will fill in the webhook url with your publicly available url.

## Posting Results

You will need to modify the `caseResults` and/or `scanResults` values to see your results on the Techcyte app. See [posting external model results](./guides/posting-external-model-results/index.md).


## Implementation tips

1. Running a GPU classifier non-stop can be expensive. Consider using a system like AWS Lambda (triggered by an API bridge event) and AWS Batch to process requests efficiently.

2. Images may be in `SVS`, `TIFF`, or `DICOM ZIP` format, handle as needed.
