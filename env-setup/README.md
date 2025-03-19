# Environment Setup Guidance

## Every Session

```bash
# Set these manually...
export GOOGLE_CLOUD_PROJECT_STAGING="<Your Google Cloud Staging Project ID>" # E.g. my-gen-ai-qa
export GOOGLE_CLOUD_PROJECT="<Your Google Cloud Project ID>" # E.g. my-gen-ai
export GOOGLE_CLOUD_REGION="<your region>"
export AGENT_NAME="<your agent>"
export REPO_NAME="<your repo>"
export REMOTE_ENGINE_ID="<your engine id>"
export BUCKET_NAME="<your bucket>"

# Or load from .env if you have one
source .env

gcloud auth login # authenticate yourself to gcloud
```

### Google Project Creation

Create destination Google projects.

Then: enable APIs and set project:

```bash
# Check we're in the correct project
gcloud config list project
gcloud config set project $GOOGLE_CLOUD_PROJECT_STAGING
export PROJECT_NUMBER=$(gcloud projects describe $GOOGLE_CLOUD_PROJECT_STAGING --format="value(projectNumber)")

# Enable APIs
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  logging.googleapis.com \
  storage-component.googleapis.com \
  aiplatform.googleapis.com

# setup ADC so any locally running application can access Google APIs
# Note that credentials will be saved to ~/.config/gcloud/application_default_credentials.json
gcloud auth application-default login
gcloud auth application-default set-quota-project $GOOGLE_CLOUD_PROJECT_STAGING
```

## Prereqs

### Python Env

One time creation of a Python virtual environment (per machine):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install agent-starter-pack
```

### Local Project

One time run steps as described in [`googleCloudPlatform/agent-starter-pack`](https://github.com/GoogleCloudPlatform/agent-starter-pack).

E.g.

```bash
agent-starter-pack create $AGENT_NAME
```

This will create the local folder with sample code. You will be prompted for settings.

### Setup Git and CI/CD

1. Add .gitignore
1. Add .gitattributes

```bash
agent-starter-pack setup-cicd \
  --staging-project=$GOOGLE_CLOUD_PROJECT_STAGING \
  --prod-project=$GOOGLE_CLOUD_PROJECT \
  --cicd-project=$GOOGLE_CLOUD_PROJECT \
  --region=$GOOGLE_CLOUD_REGION \
  --repository-name=$REPO_NAME
```

This will: 

1. Create your local git repo, with sample code
1. Updates `deployment/terraform/vars/env.tfvars` with supplied runtime variables.
1. Create a GitHub repo
1. Create GitHub integration with Cloud Build

When setting up Cloud Run integration from GitHub, if integration already exists, the routine will fail to add the newly created GitHub repo to the scope of this integration. In that case, open Settings > Applications > Add your new repo to your Cloud Run scope.

Now:

```bash
# If using git crypt (optional)
sudo apt install git-crypt
git-crypt unlock path/to/git-crypt-key # If you have an existing key for decryption

# Git user information
git config --global user.email "your@email"
git config --global user.name "Your Name"

# Initial commit
git add -A
git commit -m "Initial commit"
git push --set-upstream origin main
```

## To Test Locally

You can run this every time you make a local change and want to test the application without running the CI/CD pipeline. This will also deploy the frontend UI.

```bash
cd $REPO_NAME
make install && make playground # Uses Makefile
```
