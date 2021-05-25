resource "aws_ecr_repository" "cert-retriever" {
  name = "cert-retriever"
  tags = merge(
    local.common_tags,
    { DockerHub : "dwpdigital/cert-retriever" }
  )
}

resource "aws_ecr_repository_policy" "cert-retriever" {
  repository = aws_ecr_repository.cert-retriever.name
  policy     = data.terraform_remote_state.management.outputs.ecr_iam_policy_document
}

output "ecr_example_url" {
  value = aws_ecr_repository.cert-retriever.repository_url
}
