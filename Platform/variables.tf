variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "eu-west-2"
}

variable "vpc_id" {
  description = "VPC ID for OpenSearch domain"
  type        = string  
}

variable "subnet_ids" {
  description = "Subnet IDs for OpenSearch domain"
  type        = list(string)
}

variable "aws_account_id" {
  description = "AWS Account ID"
  type        = string
}

variable "tenant_count" {
  description = "Number of tenants"
  type        = number
  default     = 1
}

variable "s3_bucket_suffix" {
  description = "Suffix for tenant S3 buckets"
  type        = string
  default     = "knowledge-bucket"
}

variable "opensearch_domain_suffix" {
  description = "Suffix for OpenSearch domain"
  type        = string
  default     = "opensearch"
}

variable "opensearch_engine_version" {
  description = "Version of OpenSearch"
  type        = string
  default     = "OpenSearch_2.3"
}

variable "opensearch_instance_type" {
  description = "OpenSearch instance type"
  type        = string
  default     = "t3.small.search"
}

variable "opensearch_volume_size" {
  description = "Volume size for OpenSearch"
  type        = number
  default     = 10
}

variable "bedrock_role_name" {
  description = "IAM Role for AWS Bedrock"
  type        = string
  default     = "bedrock-access-role"
}

variable "bedrock_policy_name" {
  description = "IAM Policy for Bedrock access"
  type        = string
  default     = "bedrock-knowledge-policy"
}

variable "kb_suffix" {
  description = "Suffix for knowledge base names"
  type        = string
  default     = "knowledge-base"
}

variable "bedrock_model_id" {
  description = "ID of AWS Bedrock foundation model"
  type        = string
  default     = "amazon.titan-text-express-v1"
}

variable "bedrock_temperature" {
  description = "Temperature setting for model inference"
  type        = number
  default     = 0.2
}

variable "bedrock_topP" {
  description = "TopP setting for model inference"
  type        = number
  default     = 0.9
}

variable "bedrock_maxTokens" {
  description = "Max tokens for response generation"
  type        = number
  default     = 512
}

variable "foundation_model_name" {
  description = "Name for the foundation model activation"
  type        = string
  default     = "bedrock-foundation-model"
}

variable "service_catalog_product_id" {
  description = "Product ID for AWS Service Catalog"
  type        = string
}

variable "service_catalog_artifact_id" {
  description = "Artifact ID for AWS Service Catalog"
  type        = string
}

variable "service_catalog_provisioned_name" {
  description = "Provisioned name for AWS Service Catalog activation"
  type        = string
  default     = "BedrockModelActivation"
}

variable "service_catalog_path_id" {
  description = "Path ID for AWS Service Catalog"
  type        = string
}

