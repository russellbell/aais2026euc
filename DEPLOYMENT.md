# West Tek Deployment Guide

## Prerequisites

1. AWS Account with appropriate permissions
2. AWS CLI configured with credentials
3. Python 3.11+
4. Node.js 18+ (for CDK)
5. Docker (for building container images)

## Initial Setup

### 1. Install Dependencies

```bash
# Install Python dependencies
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Install AWS CDK CLI
npm install -g aws-cdk

# Bootstrap CDK (first time only)
cdk bootstrap aws://ACCOUNT-ID/REGION
```

### 2. Configure Context

Create `cdk.context.json` or pass via command line:

```json
{
  "account": "YOUR_AWS_ACCOUNT_ID",
  "region": "us-east-1"
}
```

Or use environment variables:
```bash
export CDK_DEFAULT_ACCOUNT=YOUR_AWS_ACCOUNT_ID
export CDK_DEFAULT_REGION=us-east-1
```

## Deployment Steps

### Phase 1: Infrastructure Foundation

```bash
# Synthesize CloudFormation templates
cdk synth

# Deploy all stacks
cdk deploy --all

# Or deploy individually
cdk deploy WestTekNetwork
cdk deploy WestTekStorage
cdk deploy WestTekAuth
cdk deploy WestTekCompute
cdk deploy WestTekWorkspace
```

### Post-Deployment Configuration

After deployment, note the outputs:

- `UserPoolId` - For Cognito configuration
- `APILoadBalancerDNS` - Internal API endpoint (accessible from VPC only)
- `JupyterECRRepoUri` - For pushing Jupyter images
- `APIECRRepoUri` - For pushing API images
- `AppStreamFleetName` - AppStream fleet for Jupyter access
- `AppStreamStackName` - AppStream stack name
- `AppStreamURL` - URL for AppStream authentication

### Create Initial Admin User

```bash
aws cognito-idp admin-create-user \
  --user-pool-id <UserPoolId> \
  --username admin@westtekresearch.com \
  --user-attributes Name=email,Value=admin@westtekresearch.com \
  --temporary-password "TempPass123!" \
  --message-action SUPPRESS
```

## Building and Pushing Container Images

### API Container

```bash
cd backend
docker build -t west-tek-api .
docker tag west-tek-api:latest <APIECRRepoUri>:latest

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <APIECRRepoUri>

docker push <APIECRRepoUri>:latest
```

### Jupyter Container

```bash
cd jupyter
docker build -t west-tek-jupyter .
docker tag west-tek-jupyter:latest <JupyterECRRepoUri>:latest
docker push <JupyterECRRepoUri>:latest
```

## Updating Services

After pushing new images:

```bash
# Force new deployment
aws ecs update-service \
  --cluster <ClusterName> \
  --service APIService \
  --force-new-deployment
```

## Monitoring

- CloudWatch Logs: `/aws/ecs/api` and `/aws/ecs/jupyter`
- ECS Console: Monitor task health and scaling
- ALB Target Groups: Check health check status

## Cleanup

```bash
# Destroy all resources (WARNING: This deletes everything)
cdk destroy --all
```

Note: S3 buckets, ECR repos, and EFS with RETAIN policy must be manually deleted.

## Next Steps

- Build and deploy API application (Phase 2)
- Build and deploy frontend (Phase 2)
- Configure AppStream 2.0 image with browser for Jupyter access (Phase 3)
- Configure Bedrock agents (Phase 3.5)
- Set up user access to AppStream fleet (Phase 3)
