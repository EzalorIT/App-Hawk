resource "aws_s3_bucket" "tenant" {
  count  = var.tenant_count
  bucket = "tenant-${count.index}-${var.s3_bucket_suffix}"
}

resource "aws_security_group" "opensearch_sg" {
  name        = "opensearch-sg"
  description = "Security group for OpenSearch"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [""]  
  }
}

resource "aws_opensearch_domain" "tenant" {
  count          = var.tenant_count
  domain_name    = "tenant-${count.index}-${var.opensearch_domain_suffix}"
  engine_version = var.opensearch_engine_version
  
  cluster_config {
    instance_type = var.opensearch_instance_type
  }
  ebs_options {
    ebs_enabled = true
    volume_size = var.opensearch_volume_size
  }

  node_to_node_encryption {
    enabled = true

  } 
  encrypt_at_rest {
    enabled = true
  }
    domain_endpoint_options {
        enforce_https = true
        tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
    }
    
    vpc_options {
        security_group_ids = [aws_security_group.opensearch_sg.id]
        subnet_ids = var.subnet_ids
    }
}



resource "aws_iam_role" "bedrock_role" {
  name = var.bedrock_role_name
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "bedrock.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}


resource "aws_iam_policy" "bedrock_policy" {
  name        = var.bedrock_policy_name
  description = "Policy to access knowledge base in S3 and OpenSearch"
  policy      = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::tenant-*-knowledge-bucket/*"
    },
    {
      "Effect": "Allow",
      "Action": "es:ESHttpPost",
      "Resource": "arn:aws:es:${var.aws_region}:${var.aws_account_id}:domain/tenant-*-opensearch/*"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "bedrock_attachment" {
  role       = aws_iam_role.bedrock_role.name
  policy_arn = aws_iam_policy.bedrock_policy.arn
}

resource "aws_bedrock_knowledge_base" "tenant" {
  count    = var.tenant_count
  name     = "tenant-${count.index}-${var.kb_suffix}"
  role_arn = aws_iam_role.bedrock_role.arn
  storage_configuration {
    s3_configuration {
      bucket_name = aws_s3_bucket.tenant[count.index].bucket
    }
  }
  retrieval_configuration {
    opensearch_configuration {
      domain_name = aws_opensearch_domain.tenant[count.index].domain_name
    }
  }
}

resource "aws_bedrock_model_invocation" "tenant" {
  count     = var.tenant_count
  model_id  = var.bedrock_model_id
  role_arn  = aws_iam_role.bedrock_role.arn
  parameters = <<EOT
{
  "inputText": "Provide a detailed response based on the tenant's knowledge base.",
  "temperature": ${var.bedrock_temperature},
  "topP": ${var.bedrock_topP},
  "maxTokens": ${var.bedrock_maxTokens}
}
EOT
}

