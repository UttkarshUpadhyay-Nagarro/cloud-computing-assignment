# Component Description

| Component | Purpose | Security and availability |
|---|---|---|
| IAM | Developer group and workload identities | Least-privilege group policy scoped to only the services this project uses; EC2 and Lambda use separate execution roles, not the developer group's credentials |
| VPC | Network boundary | Two AZs and isolated subnet tiers (public, private application, private database) |
| Internet Gateway | Public ALB ingress | Only public subnets route directly to it |
| NAT Gateway | Private-subnet internet egress | Lets EC2 and Lambda reach AWS APIs not covered by VPC endpoints (e.g. Systems Manager); billable, accepted for a fully working deployment |
| VPC Endpoints (S3 gateway, Secrets Manager and CloudWatch Logs interfaces) | Private-subnet access to specific AWS APIs without routing through the internet | Interface endpoints restricted by a dedicated security group |
| ALB | HTTP entry point | Multi-AZ public subnets and health checks |
| EC2 Auto Scaling Group | Hosts the upload service | Two private instances, min 2/max 4, ALB health checks |
| S3 | Durable document storage | Block public access, SSE-S3 encryption, accessed from private subnets via VPC gateway endpoint |
| Lambda | Event processing | S3 `ObjectCreated` trigger scoped to the `uploads/` prefix, runs inside the private application subnets, writes to CloudWatch Logs |
| RDS PostgreSQL | Metadata persistence | Private database subnets, no public access, storage encrypted at rest, port 5432 reachable only from the Lambda security group |
| Secrets Manager | Database credentials | Lambda reads the secret at runtime; credentials are never stored in code |
| CloudWatch | Lambda logs, dashboard, and alarms | Log output includes file name and content type; alarms watch Lambda errors, ALB 5xx responses, and RDS CPU |

## Traffic flow

Customer HTTP traffic reaches the ALB, which forwards it to healthy private EC2 instances. The application uploads directly to the private S3 bucket using its instance role. S3 invokes Lambda for objects under the `uploads/` prefix. Lambda calls `HeadObject` to read the actual `Content-Type`, reads database credentials from Secrets Manager, and inserts the file name, content type, and UTC timestamp into RDS.

## Scope and assumptions

- Single AWS region.
- Demonstration uses HTTP as explicitly permitted by the assignment; a production deployment should use HTTPS with an ACM certificate.
- RDS is single-AZ to control cost. A production version should enable Multi-AZ.
- A NAT Gateway is deployed to give private-subnet resources a path to AWS APIs not covered by the S3, Secrets Manager, and CloudWatch Logs VPC endpoints already in the stack (e.g. Systems Manager).
- Upload size is limited to 10 MB in the sample service.
- Authentication, virus scanning, document retention, and customer claim authorization are outside MVP scope.
