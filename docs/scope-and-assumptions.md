# Scope and Assumptions

## Region and environment

- Single AWS region. No multi-region failover.
- One environment only (no separate dev/stage/prod).

## Free Tier and cost trade-offs

- RDS runs as `db.t3.micro`, single-AZ, with minimal backup retention, to minimize cost and allow fast teardown. A production deployment should enable Multi-AZ and automated backups.
- A NAT Gateway is deployed alongside the VPC endpoints (S3 gateway, Secrets Manager and CloudWatch Logs interfaces). The endpoints cover the specific AWS APIs Lambda and EC2 need day to day; the NAT Gateway covers everything else a private-subnet resource might need to reach (for example, Systems Manager for operational access). This is a deliberate cost trade-off for a fully working, verifiable deployment during the evaluation window, in line with the assignment's own note that a NAT Gateway may not be free-tier eligible.
- ALB, EC2 (2x t3.micro), the NAT Gateway, interface VPC endpoints, and RDS are billable outside Free Tier limits if left running; all resources are deleted immediately after recording the required demonstrations.

## Database engine

- Amazon RDS for PostgreSQL was chosen over MySQL for native JSON/UUID support and straightforward Python connectivity via `psycopg2`.

## Security and access

- A dedicated IAM group and user, scoped only to the services this project uses (EC2, ELB, ASG, S3, Lambda, RDS, Secrets Manager, CloudWatch, SNS) plus the narrow IAM actions needed to manage the EC2/Lambda execution roles, is used for all account work — not the AWS account root user.
- The database is reachable only from the Lambda function's security group on port 5432; it has no public endpoint.
- The EC2 instance role can only `PutObject`/`ListBucket` on the uploads bucket and read the deployment bundle; it has no RDS or Secrets Manager permission.

## Application scope

- No authentication, authorization, or customer identity is implemented — any visitor can upload a file. This is out of scope for the MVP per the assignment brief.
- No virus/malware scanning of uploaded documents.
- No document retention policy or lifecycle rules on the S3 bucket.
- Upload size is capped at 10 MB.
- Traffic is served over plain HTTP, as explicitly permitted by the assignment; a production deployment should terminate TLS at the ALB using an ACM certificate.

## Known simplifications

- The application backend is a minimal Python standard-library HTTP server (no framework) to avoid needing a build step or extra runtime dependencies on the EC2 AMI.
- The Lambda function creates its own database table (`CREATE TABLE IF NOT EXISTS`) on first invocation rather than using a separate migration step.
