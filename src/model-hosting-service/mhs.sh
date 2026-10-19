#!/usr/bin/env bash
# Manage Techcyte Model Hosting Service images and containers with an API client: create images and
# push to them, and create, update, list and delete containers that run them.
set -euo pipefail

usage() {
	cat >&2 <<EOF
Usage: $(basename "$0") <command> --client-id ID --client-secret SECRET --host HOST [options]

Images:
  image create   [--name NAME] [--details TEXT]               Create an image; prints its ID
  image push     LOCAL_IMAGE [--image-id ID] [--name NAME] [--details TEXT]
                                                              Push a local image (creates an image unless --image-id)
  image login    [--image-id ID] [--name NAME] [--details TEXT]
                                                              Only docker login; prints the URI to push to
  image update   --image-id ID [--name NAME] [--details TEXT] Change an image's name and/or details
  image list                                                  List images
  image delete   --image-id ID                                Delete an image

Containers:
  container create  --name NAME --image-id ID --instance-type TYPE [--details TEXT] [--env KEY=VALUE ...]
                                                              Create a container; prints its ID
  container update  --container-id ID [--name NAME] [--details TEXT] [--image-id ID] [--instance-type TYPE]
                    [--env KEY=VALUE ...] [--unset-env KEY ...]
                                                              Change a container; anything not passed is kept
  container list                                              List containers
  container delete  --container-id ID                         Delete a container

Every command takes:
  --client-id ID          API client ID                         (or \$TECHCYTE_CLIENT_ID)
  --client-secret SECRET  API client secret                     (or \$TECHCYTE_CLIENT_SECRET)
  --host HOST             Techcyte host, e.g. app.techcyte.com  (or \$TECHCYTE_HOST)

Notes:
  --image-id and --container-id are the IDs from the page URLs (/model_hosting_service/images/<ID>)
    or from the create commands' output.
  --env can be repeated. On update it adds or replaces that variable; --unset-env removes one.
  --instance-type is one of: g4dn_xlarge g4dn_2xlarge g4dn_4xlarge g5_2xlarge g5_4xlarge g6_2xlarge
    g6_4xlarge g6e_2xlarge
  Options take their value as the next argument (--host app.techcyte.com) or after = (--host=app.techcyte.com).
  image push/login use your normal Docker config (\$DOCKER_CONFIG, default ~/.docker).
  Requires bash, curl and jq, plus docker for image push/login.
EOF
	exit "${1:-1}"
}

die() {
	echo "error: $*" >&2
	exit 1
}

CLIENT_ID="${TECHCYTE_CLIENT_ID:-}"
CLIENT_SECRET="${TECHCYTE_CLIENT_SECRET:-}"
HOST="${TECHCYTE_HOST:-}"
NAME=""
NAME_SET=""
DETAILS=""
DETAILS_SET=""
IMAGE_ID=""
CONTAINER_ID=""
INSTANCE_TYPE=""
LOCAL_IMAGE=""
ENV_SET='{}'
ENV_UNSET='[]'
GIVEN=()

for cmd in curl jq; do
	command -v "$cmd" >/dev/null || die "'$cmd' is required but was not found on PATH"
done

[[ $# -gt 0 ]] || usage
[[ "$1" == --help ]] && usage 0
[[ $# -ge 2 && "$2" != --* ]] || { echo "error: expected a command like 'image push' or 'container list'" >&2; usage; }
COMMAND="$1 $2"
shift 2

# getopts has no long options and BSD getopt (macOS) can't parse them, so parse by hand.
while [[ $# -gt 0 ]]; do
	opt="$1"
	shift
	# Split --flag=value into the flag and its value
	if [[ "$opt" == --*=* ]]; then
		set -- "${opt#*=}" "$@"
		opt="${opt%%=*}"
	fi
	case "$opt" in
		--help) usage 0 ;;
		--client-id | --client-secret | --host | --name | --details | --image-id | --container-id | --instance-type | --env | --unset-env)
			[[ $# -gt 0 ]] || { echo "error: $opt needs a value" >&2; usage; }
			value="$1"
			shift
			# An unset shell variable (--client-id "$CLIENT_ID") arrives as an empty string; --details "" clears the details
			if [[ -z "$value" && "$opt" != --details ]]; then
				die "$opt was given an empty value; if you passed a shell variable, check that it is set"
			fi
			GIVEN+=("$opt")
			case "$opt" in
				--client-id) CLIENT_ID="$value" ;;
				--client-secret) CLIENT_SECRET="$value" ;;
				--host) HOST="$value" ;;
				--name) NAME="$value" NAME_SET=1 ;;
				--details) DETAILS="$value" DETAILS_SET=1 ;;
				--image-id) IMAGE_ID="$value" ;;
				--container-id) CONTAINER_ID="$value" ;;
				--instance-type) INSTANCE_TYPE="$value" ;;
				--env)
					[[ "$value" == ?*=* ]] || die "--env takes KEY=VALUE, got '$value'"
					ENV_SET="$(jq -c --arg k "${value%%=*}" --arg v "${value#*=}" '.[$k] = $v' <<<"$ENV_SET")"
					;;
				--unset-env) ENV_UNSET="$(jq -c --arg k "$value" '. + [$k]' <<<"$ENV_UNSET")" ;;
			esac
			;;
		--*)
			echo "error: unknown option '$opt'" >&2
			usage
			;;
		*)
			[[ "$COMMAND" == "image push" && -z "$LOCAL_IMAGE" ]] || die "unexpected argument '$opt'"
			LOCAL_IMAGE="$opt"
			;;
	esac
done

case "$COMMAND" in
	"image create") ALLOWED="--name --details" ;;
	"image push" | "image login") ALLOWED="--image-id --name --details" ;;
	"image update") ALLOWED="--image-id --name --details" ;;
	"image list" | "container list") ALLOWED="" ;;
	"image delete") ALLOWED="--image-id" ;;
	"container create") ALLOWED="--name --details --image-id --instance-type --env" ;;
	"container update") ALLOWED="--container-id --name --details --image-id --instance-type --env --unset-env" ;;
	"container delete") ALLOWED="--container-id" ;;
	*)
		echo "error: unknown command '$COMMAND'" >&2
		usage
		;;
esac
for opt in "${GIVEN[@]+"${GIVEN[@]}"}"; do
	case " --client-id --client-secret --host $ALLOWED " in
		*" $opt "*) ;;
		*) die "$opt doesn't apply to '$COMMAND'" ;;
	esac
done

[[ -n "$CLIENT_ID" ]] || { echo "error: --client-id (or \$TECHCYTE_CLIENT_ID) is required" >&2; usage; }
[[ -n "$CLIENT_SECRET" ]] || { echo "error: --client-secret (or \$TECHCYTE_CLIENT_SECRET) is required" >&2; usage; }
[[ -n "$HOST" ]] || { echo "error: --host (or \$TECHCYTE_HOST) is required" >&2; usage; }
case "$COMMAND" in
	"image push") [[ -n "$LOCAL_IMAGE" ]] || die "image push needs the local image to push, e.g. image push my-model:latest" ;;
	"image update" | "image delete") [[ -n "$IMAGE_ID" ]] || die "--image-id is required" ;;
	"container create")
		[[ -n "$NAME" ]] || die "--name is required"
		[[ -n "$IMAGE_ID" ]] || die "--image-id is required"
		[[ -n "$INSTANCE_TYPE" ]] || die "--instance-type is required"
		;;
	"container update" | "container delete") [[ -n "$CONTAINER_ID" ]] || die "--container-id is required" ;;
esac
if [[ "$COMMAND" == "image update" && -z "$NAME_SET" && -z "$DETAILS_SET" ]]; then
	die "image update needs --name and/or --details"
fi

if [[ "$COMMAND" == "image push" || "$COMMAND" == "image login" ]]; then
	command -v docker >/dev/null || die "'docker' is required but was not found on PATH"
	docker info >/dev/null 2>&1 || die "cannot reach the Docker daemon; is Docker running?"
	if [[ -n "$LOCAL_IMAGE" ]]; then
		docker image inspect "$LOCAL_IMAGE" >/dev/null 2>&1 || die "local image '$LOCAL_IMAGE' not found; build it first"
	fi
fi

# Accept "app.techcyte.com", "https://app.techcyte.com/", etc.
HOST="${HOST#http://}"
HOST="${HOST#https://}"
HOST="${HOST%%/*}"

# The host's config.json says where the API and depot live; fall back to the usual layout.
CONFIG="$(curl -fsS "https://$HOST/config.json" 2>/dev/null || echo '{}')"
jq -e 'type == "object"' <<<"$CONFIG" >/dev/null 2>&1 || CONFIG='{}'
BASE_URL="$(jq -r --arg d "https://$HOST" '.baseURL // $d' <<<"$CONFIG")"
DEPOT_URL="$(jq -r '.externalContainerDepotURL // "/api/external-container-depot/graphql"' <<<"$CONFIG")"
# Deployed configs give the depot as a path relative to the host.
[[ "$DEPOT_URL" == /* ]] && DEPOT_URL="https://$HOST$DEPOT_URL"

echo "Authenticating against $BASE_URL ..." >&2
TOKEN_RESPONSE="$(curl -sS -X POST "$BASE_URL/api/v3/token" \
	--data-urlencode "grant_type=client_credentials" \
	--data-urlencode "client_id=$CLIENT_ID" \
	--data-urlencode "client_secret=$CLIENT_SECRET")"
TOKEN="$(jq -r '.access_token // empty' <<<"$TOKEN_RESPONSE" 2>/dev/null || true)"
[[ -n "$TOKEN" ]] || die "failed to get a token (check the client ID, secret and host): $TOKEN_RESPONSE"

# gql QUERY VARIABLES_JSON -> prints .data, exits on GraphQL/HTTP errors
gql() {
	local body response
	body="$(jq -n --arg q "$1" --argjson v "$2" '{query: $q, variables: $v}')"
	response="$(curl -sS -X POST "$DEPOT_URL" \
		-H "Content-Type: application/json" \
		-H "Authorization: Bearer $TOKEN" \
		-d "$body")"
	if ! jq -e '.data and ((.errors // []) | length == 0)' <<<"$response" >/dev/null 2>&1; then
		die "request to $DEPOT_URL failed: $response"
	fi
	jq '.data' <<<"$response"
}

# get_node ID FIELDS -> prints the node, exits if it doesn't exist
get_node() {
	local data
	data="$(gql "query node(\$id: ID!) { node(id: \$id) { __typename $2 } }" "$(jq -n --arg id "$1" '{id: $id}')")"
	jq -e '.node' <<<"$data" >/dev/null || die "$1 not found"
	jq '.node' <<<"$data"
}

# Unset strings become null, so the server applies its defaults
create_image() {
	echo "Creating image ..." >&2
	local vars
	vars="$(jq -n --arg name "$NAME" --arg details "$DETAILS" \
		'{input: {name: (if $name == "" then null else $name end), details: (if $details == "" then null else $details end)}}')"
	IMAGE_ID="$(gql 'mutation createImage($input: CreateImageInput!) { createImage(input: $input) { id } }' "$vars" |
		jq -r '.createImage.id')"
	echo "Created image $IMAGE_ID (pass --image-id $IMAGE_ID to reuse it)" >&2
}

# renameImage needs the name and replaces the details, so fill in whichever wasn't passed from the current image
update_image() {
	echo "Updating image $IMAGE_ID ..." >&2
	local current vars
	current="$(get_node "$IMAGE_ID" '... on Image { name details }')"
	[[ -n "$NAME_SET" ]] || NAME="$(jq -r '.name' <<<"$current")"
	[[ -n "$DETAILS_SET" ]] || DETAILS="$(jq -r '.details // ""' <<<"$current")"
	vars="$(jq -n --arg id "$IMAGE_ID" --arg name "$NAME" --arg details "$DETAILS" \
		'{input: {id: $id, name: $name, details: $details}}')"
	gql 'mutation renameImage($input: RenameImageInput!) { renameImage(input: $input) { id } }' "$vars" >/dev/null
	echo "Updated image $IMAGE_ID" >&2
}

# Sets PUSH_URI and REGISTRY
ecr_login() {
	echo "Generating registry credentials ..." >&2
	local creds username password repo tag
	creds="$(gql 'mutation generateEcrCredentials($input: GenerateEcrCredentialsInput!) {
		generateEcrCredentials(input: $input) { username password region awsEcrRepo tag }
	}' "$(jq -n --arg id "$IMAGE_ID" '{input: {id: $id}}')")"
	username="$(jq -r '.generateEcrCredentials.username' <<<"$creds")"
	password="$(jq -r '.generateEcrCredentials.password' <<<"$creds")"
	repo="$(jq -r '.generateEcrCredentials.awsEcrRepo' <<<"$creds")"
	tag="$(jq -r '.generateEcrCredentials.tag' <<<"$creds")"
	REGISTRY="${repo%%/*}"
	PUSH_URI="$repo:$tag"
	if ! [[ "$tag" =~ ^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$ ]]; then
		die "the server returned a tag Docker can't use ('$tag'); please contact Techcyte support"
	fi
	if ! printf '%s' "$password" | docker login --username "$username" --password-stdin "$REGISTRY" >&2; then
		cat >&2 <<EOF
error: docker login to $REGISTRY failed. If the error above mentions a credential helper or
credential store, check "credsStore" and "credHelpers" in ${DOCKER_CONFIG:-$HOME/.docker}/config.json.
EOF
		exit 1
	fi
}

# environmentVars comes back as a JSON string (AWSJSON), or null
ENV_FROM_SERVER='if . == null then {} elif type == "string" then fromjson else . end'

case "$COMMAND" in
	"image create")
		create_image
		echo "$IMAGE_ID"
		;;

	"image update")
		update_image
		echo "$IMAGE_ID"
		;;

	"image push" | "image login")
		if [[ -z "$IMAGE_ID" ]]; then
			create_image
		elif [[ -n "$NAME_SET" || -n "$DETAILS_SET" ]]; then
			update_image
		fi
		ecr_login
		if [[ "$COMMAND" == "image push" ]]; then
			docker tag "$LOCAL_IMAGE" "$PUSH_URI"
			docker push "$PUSH_URI" >&2
			# The login is only needed for the push; don't leave it lying around.
			docker logout "$REGISTRY" >/dev/null 2>&1 || true
			echo "Pushed $LOCAL_IMAGE to $PUSH_URI (image ID $IMAGE_ID)" >&2
		else
			cat >&2 <<EOF

Logged in (valid for 12 hours). Image ID: $IMAGE_ID
Push with:
  docker tag my-docker-image:latest $PUSH_URI
  docker push $PUSH_URI

Or run "$(basename "$0") image push my-docker-image:latest --image-id $IMAGE_ID" to tag and push in one step.

EOF
		fi
		# The push URI alone on stdout, so it can be captured: URI=$(mhs.sh image login ...)
		echo "$PUSH_URI"
		;;

	"image list")
		gql 'query images { images { edges { node { id name status createdAt details } } } }' '{}' |
			jq -r '["ID", "NAME", "STATUS", "CREATED", "DETAILS"],
				(.images.edges[].node | [.id, .name, .status, .createdAt, (.details // "")]) | @tsv'
		;;

	"image delete")
		DELETED="$(gql 'mutation deleteImages($input: DeleteImagesInput!) { deleteImages(input: $input) { id } }' \
			"$(jq -n --arg id "$IMAGE_ID" '{input: {ids: [$id]}}')")"
		jq -e '.deleteImages[0]' <<<"$DELETED" >/dev/null || die "image $IMAGE_ID not found"
		echo "Deleted image $IMAGE_ID" >&2
		;;

	"container create")
		echo "Creating container ..." >&2
		VARS="$(jq -n --arg name "$NAME" --arg image "$IMAGE_ID" --arg type "$INSTANCE_TYPE" --argjson env "$ENV_SET" \
			'{input: {name: $name, image: $image, instanceType: $type,
				environmentVars: (if $env == {} then null else ($env | tojson) end)}}')"
		CONTAINER_ID="$(gql 'mutation createContainer($input: CreateContainerInput!) { createContainer(input: $input) { id } }' "$VARS" |
			jq -r '.createContainer.id')"
		echo "Created container $CONTAINER_ID" >&2
		# createContainer has no details field, so set them with an update
		if [[ -n "$DETAILS" ]]; then
			VARS="$(jq -n --arg id "$CONTAINER_ID" --arg name "$NAME" --arg details "$DETAILS" --arg image "$IMAGE_ID" \
				--arg type "$INSTANCE_TYPE" --argjson env "$ENV_SET" \
				'{input: {id: $id, name: $name, details: $details, image: $image, instanceType: $type, environmentVars: ($env | tojson)}}')"
			gql 'mutation updateContainer($input: UpdateContainerInput!) { updateContainer(input: $input) { id } }' "$VARS" >/dev/null
		fi
		echo "$CONTAINER_ID"
		;;

	"container update")
		echo "Updating container $CONTAINER_ID ..." >&2
		# updateContainer replaces every field, so start from the current container
		CURRENT="$(get_node "$CONTAINER_ID" '... on Container { name details image instanceType environmentVars }')"
		VARS="$(jq -n --argjson c "$CURRENT" --arg id "$CONTAINER_ID" \
			--arg name "$NAME" --arg nameSet "$NAME_SET" --arg details "$DETAILS" --arg detailsSet "$DETAILS_SET" \
			--arg image "$IMAGE_ID" --arg type "$INSTANCE_TYPE" --argjson set "$ENV_SET" --argjson unset "$ENV_UNSET" \
			"{input: {
				id: \$id,
				name: (if \$nameSet != \"\" then \$name else \$c.name end),
				details: (if \$detailsSet != \"\" then \$details else (\$c.details // \"\") end),
				image: (if \$image != \"\" then \$image else \$c.image end),
				instanceType: (if \$type != \"\" then \$type else \$c.instanceType end),
				environmentVars: ((\$c.environmentVars | $ENV_FROM_SERVER) + \$set | delpaths(\$unset | map([.])) | tojson)
			}}")"
		gql 'mutation updateContainer($input: UpdateContainerInput!) { updateContainer(input: $input) { id } }' "$VARS" >/dev/null
		echo "Updated container $CONTAINER_ID" >&2
		echo "$CONTAINER_ID"
		;;

	"container list")
		gql 'query containers { containers { edges { node { id name image instanceType environmentVars } } } }' '{}' |
			jq -r "[\"ID\", \"NAME\", \"IMAGE_ID\", \"INSTANCE_TYPE\", \"ENV\"],
				(.containers.edges[].node | [.id, .name, .image, .instanceType,
					(.environmentVars | $ENV_FROM_SERVER | to_entries | map(\"\(.key)=\(.value)\") | join(\" \"))]) | @tsv"
		;;

	"container delete")
		DELETED="$(gql 'mutation deleteContainers($input: DeleteContainersInput!) { deleteContainers(input: $input) { id } }' \
			"$(jq -n --arg id "$CONTAINER_ID" '{input: {ids: [$id]}}')")"
		jq -e '.deleteContainers[0]' <<<"$DELETED" >/dev/null || die "container $CONTAINER_ID not found"
		echo "Deleted container $CONTAINER_ID" >&2
		;;
esac
