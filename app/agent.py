# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# mypy: disable-error-code="union-attr"
import json
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_google_vertexai import ChatVertexAI
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

# LOCATION = "europe-west1"
LOCATION = "global"
LLM = "gemini-2.5-flash-preview-04-17"

# 1. Define tools
@tool
def generate_terraform_example(resource_type: str) -> str:
    """Provides an example Terraform configuration for a given resource type."""
    examples = {
        "google_compute_instance": """resource "google_compute_instance" "default" {
  name         = "vm-instance"
  machine_type = "e2-medium"
  zone         = "europe-west1-a"

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
    }
  }

  network_interface {
    network = "default"
    access_config {
      // Ephemeral public IP
    }
  }
}""",
        "google_storage_bucket": """resource "google_storage_bucket" "default" {
  name          = "example-bucket"
  location      = "EU"
  force_destroy = true

  uniform_bucket_level_access = true
}""",
        "google_cloud_run_service": """resource "google_cloud_run_service" "default" {
  name     = "cloudrun-service"
  location = "europe-west1"

  template {
    spec {
      containers {
        image = "eu-docker.pkg.dev/cloudrun/container/hello"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}"""
    }
    
    return examples.get(resource_type, "Resource type not found. Try 'google_compute_instance', 'google_storage_bucket', or 'google_cloud_run_service'.")


@tool
def create_terraform_files(terraform_files: dict) -> str:
    """
    Formats Terraform configuration files for display and download.
    
    Args:
        terraform_files: Dictionary with filenames as keys and file contents as values
                         Example: {"main.tf": "...", "variables.tf": "..."}
    
    Returns:
        Formatted terraform files for display
    """
    from datetime import datetime
    
    # Format the files for display
    formatted_output = f"""# Terraform Configuration
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This contains Terraform configuration files generated from your architecture document.

## Files
"""
    # Add each file name
    for filename in terraform_files.keys():
        formatted_output += f"- {filename}\n"
    
    # Add each file content
    for filename, content in terraform_files.items():
        formatted_output += f"\n## {filename}\n```hcl\n{content}\n```\n"
    
    return formatted_output


tools = [generate_terraform_example, create_terraform_files]


# 2. Set up the language model
try:
    llm = ChatVertexAI(
        model=LLM, location=LOCATION, temperature=0, streaming=True
    ).bind_tools(tools)
except Exception as e:
    import logging
    logging.warning(f"Error initializing Vertex AI model: {e}")
    # Fallback to a simpler configuration
    llm = ChatVertexAI(
        model="gemini-2.5-pro-preview-05-06", location=LOCATION, temperature=0, max_tokens=4096
    ).bind_tools(tools)

# 3. Define workflow components
def should_continue(state: MessagesState) -> str:
    """Determines whether to use tools or end the conversation."""
    last_message = state["messages"][-1]
    return "tools" if last_message.tool_calls else END

def call_model(state: MessagesState, config: RunnableConfig) -> dict[str, BaseMessage]:
    """Calls the language model and returns the response."""
    system_message = """You are a specialized Infrastructure-as-Code assistant that generates Terraform configurations based on architecture requirements or documents.

Your capabilities:
1. You can analyze PDF or image documents that users upload to identify infrastructure components.
2. You can generate Terraform code for Google Cloud resources.
3. You can create complete Terraform projects, including main.tf, variables.tf, and outputs.tf files, but others as required.

When a user uploads a PDF or describes their infrastructure:
- Identify computing resources (VMs, Cloud Run, GKE, etc.)
- Identify storage components (GCS, databases)
- Identify networking components (VPC, firewall rules)
- Identify security configurations (IAM roles, service accounts)
- Identify any other Google Cloud resources, such as Pub/Sub, Cloud Composer, etc.
- Generate appropriate Terraform code for the identified components. 

To present the Terraform code:
1. Generate a complete set of Terraform files (e.g. main.tf, variables.tf, outputs.tf)
2. Use the create_terraform_files tool to format them for display
3. Explain what infrastructure components you identified and why

Always adhere to Terraform best practices:
- Use variables for environment-specific values
- Follow proper naming conventions
- Include detailed comments in the code
- Organize resources logically
"""
    messages_with_system = [{"type": "system", "content": system_message}] + state[
        "messages"
    ]
    # Forward the RunnableConfig object to ensure the agent is capable of streaming the response.
    response = llm.invoke(messages_with_system, config)
    return {"messages": response}

# 4. Create the workflow graph
workflow = StateGraph(MessagesState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))
workflow.set_entry_point("agent")

# 5. Define graph edges
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

# 6. Compile the workflow
agent = workflow.compile()
