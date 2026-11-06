# Optional AWS deployment — not implemented
No apply-ready Terraform stack is included. Do not assume AWS deployment has been verified.
Suggested target: ECS Fargate API/web/worker, RDS PostgreSQL with vector extension,
ElastiCache Redis, private S3, ALB + ACM, Secrets Manager, CloudWatch and an OTel collector.
Before implementation, choose region, retention rules, budget, network topology, and recovery objectives.
Do not expose database, Redis, or buckets publicly. Use task IAM roles rather than static S3 credentials.
