"""
Example script to get objects from an evaluation

Should have CLIENT_ID and CLIENT_SECRET in the environment variables.
"""

import requests
from urllib.parse import urljoin
import os
import json
import argparse


if __name__ == "__main__":

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Get objects from an evaluation")
    parser.add_argument("scan_id", help="The scan ID (previously sample ID)")
    parser.add_argument("evaluation_id", help="The evaluation ID")
    parser.add_argument("save_location", help="The save location for the JSON file")
    args = parser.parse_args()

    # parameters
    host = "https://api.ci.techcyte.com"

    assert not os.path.exists(args.save_location), "File already exists"

    # Get a auth token
    session = requests.Session()
    response = session.request(
        "POST",
        urljoin(host, "/api/v3/token"),
        data={
            "grant_type": "client_credentials",
            "client_id": os.getenv("CLIENT_ID"),
            "client_secret": os.getenv("CLIENT_SECRET"),
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
        },
    ).json()
    assert "access_token" in response, "Failed to get a JWT from techcyte-server."
    access_token = response["access_token"]

    # Get objects
    response = session.request(
        "POST",
        urljoin(host, "/api/graphql"),
        json={
            "query": """
                query($sample_id: String!, $evaluation_id: String!) {
                    objects(sample_id: $sample_id, filter: { evaluation_id: $evaluation_id }) {
                        confidence
                        height
                        width
                        x
                        y
                    }
                }
            """,
            "variables": {
                "evaluation_id": args.evaluation_id,
                "sample_id": args.scan_id,
            },
        },
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
    )

    # save objects
    with open(args.save_location, "w") as f:
        objects = response.json()["data"]["objects"]
        print(f"Saved {len(objects)} objects to {args.save_location}")
        json.dump(objects, f, indent=4)
