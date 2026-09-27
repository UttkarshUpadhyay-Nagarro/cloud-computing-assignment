# NAGP Cloud Document Portal

This package implements the workshop case study: a public upload portal on EC2, S3 object storage, S3-triggered Lambda processing, and a private RDS PostgreSQL database.

## Repository layout

- `app/`: Python (standard library) upload service and browser UI, run on EC2.
- `lambda/`: S3 processor that reads `HeadObject` metadata and inserts file name, content type, and timestamp into RDS.
- `architecture.mmd`: architecture diagram source (Mermaid).
- `iam/deployment-policy.json`: least-privilege IAM policy for the workshop's deployment/developer group.
- `docs/`: component description and scope and assumptions documents.

## Architecture

- One VPC (`10.0.0.0/16`) spans two Availability Zones with three subnet tiers: 2 public, 2 private application, 2 private database subnets.
- The Application Load Balancer is internet-facing in the public subnets; EC2 instances run in the private application subnets behind an Auto Scaling Group.
- RDS runs in the private database subnets with no public access.
- Private-subnet resources reach S3, Secrets Manager, and CloudWatch Logs through dedicated VPC endpoints, and reach other AWS APIs (such as Systems Manager) through a NAT Gateway.

### Security

- Security groups form a strict chain: only the ALB accepts inbound HTTP from the internet; only the ALB's security group may reach the EC2 instances on port 3000; only the Lambda function's security group may reach RDS on port 5432.
- Network ACLs allow all traffic in both directions (stateless) — access control is enforced entirely at the security-group layer, which is stateful and scoped per-resource.
- The S3 bucket blocks all public access and encrypts objects at rest (SSE-S3).
- RDS storage is encrypted at rest and is never publicly accessible.
- Database credentials live in Secrets Manager; the Lambda function retrieves them at runtime rather than storing them in code or environment variables directly.
- The EC2 instance role is limited to S3 object read/write on the upload bucket — it has no RDS or Secrets Manager permission.
- Account work is done through a dedicated IAM group and user scoped to only the services this project uses — not the AWS account root user.

## Verifying the deployment

1. Open the Application Load Balancer's URL in a browser.
2. Upload a document through the form.
3. Confirm the object appears in the S3 bucket under the `uploads/` prefix.
4. Confirm the Lambda function's CloudWatch log shows the file name, content type, and a successful insert.
5. Confirm the row count reported in that log entry increases with each upload.

## Design decisions

- One VPC spans two AZs with two public, two private application, and two private database subnets.
- ALB is internet-facing; EC2 instances are private and managed by an ASG.
- EC2 receives only S3 object write/list permissions. It has no RDS permission.
- Lambda is the only security-group source allowed to reach RDS on TCP/5432.
- S3 is private, encrypted with SSE-S3, and accessed from private subnets through a gateway endpoint.
- A NAT Gateway is deployed alongside the VPC endpoints so private-subnet resources have both targeted access (S3, Secrets Manager, CloudWatch Logs) and general outbound connectivity where needed.
- RDS is single-AZ for cost control; the database subnet group spans two AZs and Multi-AZ can be enabled for production.

## Submission

See `docs/component-description.md` and `docs/scope-and-assumptions.md` for the corresponding written deliverables. After recording the required demonstrations, all AWS resources created for this workshop are deleted and the account is verified to have no remaining billable services from this project.
