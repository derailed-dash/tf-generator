terraform {
  backend "gcs" {
    bucket = "tf-generator-prd-terraform-state"
    prefix = "dev"
  }
}
