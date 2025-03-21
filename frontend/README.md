# Guidance for Deploying the IaC Auto Generator Frontend

## Every Session

For local dev, always set these variables:

```bash
# Ensure all other env vars have been set, then...

export LOG_LEVEL='DEBUG'
export VERSION="0.1"
export GAR_REPO="tf-generator"
```

## Running and Testing the Application Locally

### Dev Environment Setup

One-time setup:

```bash
# Setup Python environment and install dependencies
# If you haven't got your venv already...
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running Streamlit App Locally in a Docker Container

Make sure your Docker environment is running.

```bash
# To build as a container image
docker build -t $AGENT_NAME:$VERSION .

# To run as a local container
# We need to pass environment variables to the container
# and the Google Application Default Credentials (ADC)
docker run --rm -p 8080:8080 \
  -e PROJECT_ID=$GOOGLE_CLOUD_PROJECT \
  -e REGION=$GOOGLE_CLOUD_REGION \
  -e LOG_LEVEL=$LOG_LEVEL \
  -e REMOTE_AGENT_ENGINE_ID=$REMOTE_ENGINE_ID \
  -e BUCKET_NAME=$BUCKET_NAME \
  -e GOOGLE_APPLICATION_CREDENTIALS="/app/.config/gcloud/application_default_credentials.json" \
  --mount type=bind,source=${HOME}/.config/gcloud,target=/app/.config/gcloud \
   $AGENT_NAME:$VERSION
```

## Running in Google Cloud

### Build and Push to Google Artifact Registry:

```bash
# One time setup - create a GAR repo
gcloud artifacts repositories create "$GAR_REPO" \
  --location="$GOOGLE_CLOUD_REGION" --repository-format=Docker

# Allow authentication to the repo
gcloud auth configure-docker "$GOOGLE_CLOUD_REGION-docker.pkg.dev"

# Every time we want to build a new version and push to GAR
# This will take a couple of minutes
gcloud builds submit \
  --tag "$GOOGLE_CLOUD_REGION-docker.pkg.dev/$GOOGLE_CLOUD_PROJECT/$GAR_REPO/$AGENT_NAME:$VERSION"
```

### Deploy to Cloud Run

Public service with no authentication:

```bash
# Deploy to Cloud Run - this takes a couple of minutes
# Set max-instances to 1 to minimise cost
# Add CPU boost for fast start
gcloud run deploy "$AGENT_NAME" \
  --port=8080 \
  --image="$GOOGLE_CLOUD_REGION-docker.pkg.dev/$GOOGLE_CLOUD_PROJECT/$GAR_REPO/$AGENT_NAME:$VERSION" \
  --max-instances=1 \
  --memory=1024Mi \
  --allow-unauthenticated \
  --region=$GOOGLE_CLOUD_REGION \
  --platform=managed  \
  --project=$GOOGLE_CLOUD_PROJECT \
  --cpu-boost \
  --set-env-vars=PROJECT_ID=$GOOGLE_CLOUD_PROJECT,REGION=$GOOGLE_CLOUD_REGION,LOG_LEVEL=$LOG_LEVEL,REMOTE_AGENT_ENGINE_ID=$REMOTE_ENGINE_ID,BUCKET_NAME=$BUCKET_NAME

APP_URL=$(gcloud run services describe $AGENT_NAME --platform managed --region $GOOGLE_CLOUD_REGION --format="value(status.address.url)")
echo $APP_URL
```