# environments/dev/providers.tf
provider "aws" {
  region  = "us-east-1"
  profile = "dev"

  default_tags {
    tags = {
      Environment = "dev"
      Project     = "products-catalog-api"
      ManagedBy   = "terraform"
    }
  }
}
