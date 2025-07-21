import os
import requests
from typing import Dict, Any


class TechcyteClient:
    def __init__(self):
        """Initialize the Techcyte client with the base URL and JWT token from environment."""
        host = os.environ.get("HOST")
        if not host:
            raise ValueError("HOST environment variable is not set")

        self.base_url = f"https://api.{host.rstrip('/')}/api/v3"

        self.token = os.environ.get("JWT_TOKEN")
        if not self.token:
            raise ValueError("JWT_TOKEN environment variable is not set")

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def post_results(self, task_id: str, results: Dict[str, Any]) -> requests.Response:
        """
        Post results to the /external/results/{task_id} endpoint.

        Args:
            task_id: The ID of the task
            results: Dictionary containing caseResults and scanResults as per the schema

        Returns:
            requests.Response: The response from the server

        Raises:
            requests.RequestException: If the request fails
        """
        url = f"{self.base_url}/external/results/{task_id}"
        try:
            response = requests.post(url, json=results, headers=self.headers)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            raise requests.RequestException(f"Failed to post results: {str(e)}")


# Example usage
if __name__ == "__main__":
    # Sample data matching the schema

    task_id = os.environ["TASK_ID"]
    scan_id = os.environ["SCAN_ID"]

    sample_results = {
        "caseResults": {"mitosisCount": 1000},
        "scanResults": [
            {
                "scanId": scan_id,
                "geojson": {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "bbox": [250, 100, 300, 200],
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": [
                                    [
                                        [250, 100],
                                        [250, 200],
                                        [300, 250],
                                        [300, 100],
                                        [250, 100],
                                    ]
                                ],
                            },
                            "properties": {"annotation_type": "tissue_tumor_positive"},
                        },
                    ],
                },
            }
        ],
    }

    # Initialize client and post results
    client = TechcyteClient()
    try:
        response = client.post_results(task_id, sample_results)
        print(f"Success: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error: {str(e)}")
