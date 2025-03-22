# Environment Setup Guidance

## Google Project Creation

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
```

## Prereqs

Run on any dev machine where we're running this solution.

### Linux Packages

```bash
# Install any missing packages
sudo apt install make
sudo apt install git-crypt # (Optional, if you want to encrypt any files in the repo)
```

- Install [Google Cloud SDK](https://cloud.google.com/sdk/docs/install#linux)
- Install [Terraform](https://developer.hashicorp.com/terraform/install)

### Python Env

One time creation of a Python virtual environment (per machine):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install agent-starter-pack

git-crypt unlock path/to/key # If you have any encrypted files to unlock
```

## Every Session

Run with every session:

```bash
# Load from .env if you have one
source .env

# Or, run these and substitute your values...
# export GOOGLE_CLOUD_PROJECT_STAGING="<Your Google Cloud Staging Project ID>" # E.g. my-gen-ai-qa
# export GOOGLE_CLOUD_PROJECT="<Your Google Cloud Project ID>" # E.g. my-gen-ai
# export GOOGLE_CLOUD_REGION="<your region>"
# export AGENT_NAME="<your agent>"
# export REPO_NAME="<your repo>"
# export STAGING_REMOTE_ENGINE_ID="<your engine id>"
# export PROD_REMOTE_ENGINE_ID="<your engine id>"
# export STAGING_BUCKET_NAME="<your bucket>"
# export PROD_BUCKET_NAME="<your bucket>"

gcloud auth login # authenticate yourself to gcloud

# Check we're in the correct project
gcloud config list project
gcloud config set project $GOOGLE_CLOUD_PROJECT_STAGING
export PROJECT_NUMBER=$(gcloud projects describe $GOOGLE_CLOUD_PROJECT_STAGING --format="value(projectNumber)")

# setup ADC so any locally running application can access Google APIs
# Note that credentials will be saved to ~/.config/gcloud/application_default_credentials.json
gcloud auth application-default login
gcloud auth application-default set-quota-project $GOOGLE_CLOUD_PROJECT_STAGING
```

## Local Project Creation

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
git-crypt unlock path/to/git-crypt-key # If you have an existing key for decryption

# Git user information
git config --global user.email "your@email"
git config --global user.name "Your Name"

# Initial commit
git add -A
git commit -m "Initial commit"
git push --set-upstream origin main
```

This should trigger a build in Cloud Build immediately.  To verify, open Cloud Build in the Cloud Console, switch to the PRD project and selected region. You should see your build.

Note, if the build fails with an error like this:

```text
Your build failed to run: failed precondition: due to quota restrictions, cannot run builds in this region, see https://cloud.google.com/build/docs/locations#restricted_regions_for_some_projects
```

Then it's likely you have a quote limit on the Cloud Build API. Check in:
IAM & Admin > Quote & System Limits > Look for "Cloud Build" APIs. If any show a quota value of 0, you will need to request a quota increase.

**Now is a good time to restart your terminal.**

## To Test Locally

You can run this every time you make a local change and want to test the application without running the CI/CD pipeline. This will also deploy the frontend UI.

```bash
cd $REPO_NAME
make install && make playground # Uses Makefile
```

If you get an error running this, you probably need to restart your terminal!


