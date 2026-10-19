# Model Hosting Service

This directory has a template container for the Techcyte Model Hosting Service (`Dockerfile`, `main.py`, `techcyte_client.py`) and `mhs.sh`, a script for deploying it. For the template, see the [Model Hosting Service docs](https://techcyte.github.io/devkit/model-hosting-service/).

## Deploying with mhs.sh

`mhs.sh` does what the Model Hosting Service pages do, using an API client instead of the Techcyte app. It creates images and pushes to them, and creates, updates, lists and deletes containers. It needs `bash`, `curl` and `jq`, plus `docker` for pushing.

Every command needs your API client credentials (see [Creating an API key](https://techcyte.github.io/devkit/guides/creating-an-api-key/)) and your Techcyte host. Pass them as `--client-id`, `--client-secret` and `--host`, or set them once:

```
export TECHCYTE_CLIENT_ID="your-api-client-id"
export TECHCYTE_CLIENT_SECRET="your-api-client-secret"
export TECHCYTE_HOST="app.techcyte.com"
```

Build for `linux/amd64`, which the Model Hosting Service runs on. This matters on Apple Silicon Macs:

```
docker build --platform linux/amd64 -t my-docker-image:latest .
```

### Images

```
# Create an image and push to it. Prints the push URI; the image ID is in the output
./mhs.sh image push my-docker-image:latest --name "My model" --details "First version"

# Push a new version to an existing image
./mhs.sh image push my-docker-image:latest --image-id <IMAGE_ID>

# Only log in to the registry and print the URI, to tag and push yourself (the login lasts 12 hours)
URI=$(./mhs.sh image login --image-id <IMAGE_ID>)
docker tag my-docker-image:latest "$URI" && docker push "$URI"

./mhs.sh image create --name "My model"                     # prints the new image ID
./mhs.sh image update --image-id <IMAGE_ID> --details "Second version"
./mhs.sh image list
./mhs.sh image delete --image-id <IMAGE_ID>
```

### Containers

```
# Prints the new container ID
./mhs.sh container create --name "My container" --image-id <IMAGE_ID> --instance-type g4dn_xlarge \
  --env THRESHOLD=0.5 --env MODE=fast

# Only the options you pass are changed. --env adds or replaces a variable, --unset-env removes one
./mhs.sh container update --container-id <CONTAINER_ID> --instance-type g5_2xlarge --env THRESHOLD=0.7 --unset-env MODE

./mhs.sh container list
./mhs.sh container delete --container-id <CONTAINER_ID>
```

### Notes

- Image and container IDs are in the page URLs on the Model Hosting Service pages (e.g. `/model_hosting_service/images/<IMAGE_ID>`), and are printed by the `create` commands and `list`.
- `--instance-type` is one of `g4dn_xlarge`, `g4dn_2xlarge`, `g4dn_4xlarge`, `g5_2xlarge`, `g5_4xlarge`, `g6_2xlarge`, `g6_4xlarge` or `g6e_2xlarge`. See the [instance types table](https://techcyte.github.io/devkit/guides/model-hosting-service/#aws-instance-types-available).
- Run `./mhs.sh --help` for every command and option.
- If `docker login` fails with a credential helper error such as `error storing credentials ... not implemented`, your Docker config sends this registry to a credential helper that can't store the login (commonly AWS's `ecr-login`). Run the script with a temporary, clean Docker config instead:
  ```
  DOCKER_CONFIG=$(mktemp -d) ./mhs.sh image push my-docker-image:latest --image-id <IMAGE_ID>
  ```
