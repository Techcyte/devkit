import base64
import requests
from typing import Dict, Any, Union


class TechcyteClient:
    def __init__(
        self,
        host: str = "app.techcyte.com",
        jwt_token: Union[str, None] = None,
        api_key_id: Union[str, None] = None,
        api_key_secret: Union[str, None] = None,
    ):
        """Initialize the Techcyte client with the base URL and JWT token or API key."""
        self.host = host
        self.base_url = f"https://api.{host.rstrip('/')}/api/v3"

        self.token = jwt_token
        self.api_key_id = api_key_id
        self.api_key_secret = api_key_secret
        if not self.token and not self.api_key_secret:
            raise ValueError(
                "Either JWT_TOKEN or API_KEY_ID+API_KEY_SECRET environment variable must be set"
            )

        if self.api_key_secret:
            self.update_token()

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def update_token(self):
        url = f"https://api.{self.host}/api/v3/token"
        # Combine api_key_id and api_key_secret with a colon and Base64 encode
        auth_string = f"{self.api_key_id}:{self.api_key_secret}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()
        headers = {
            "accept": "application/json, text/plain, */*",
            "authorization": f"Basic {auth_encoded}",
            "content-type": "application/x-www-form-urlencoded",
        }
        data = {"grant_type": "client_credentials"}

        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()  # Raise an exception for bad status codes

        self.token = response.json()["access_token"]

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

    task_id = "123"
    scan_id = "456"

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
    client = TechcyteClient(
        api_key_id="your_api_key_id_here", api_key_secret="your_api_key_secret_here"
    )
    try:
        response = client.post_results(task_id, sample_results)
        print(f"Success: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error: {str(e)}")
