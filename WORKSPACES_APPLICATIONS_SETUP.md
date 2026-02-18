# WorkSpaces Applications Setup Guide (Ubuntu Pro 24.04)

## Overview

Amazon WorkSpaces Applications with Elastic fleets powered by Ubuntu Pro 24.04 LTS provides serverless application streaming. The service automatically manages capacity without requiring you to create custom images or manage scaling policies.

## Architecture

```
User Browser → WorkSpaces Applications → Internal ALB → ECS Jupyter Tasks
```

## Key Features

- **Serverless**: No need to predict usage or manage scaling
- **Ubuntu Pro 24.04 LTS**: Enterprise-grade Linux with extended security
- **Elastic Fleet**: AWS-managed pool of streaming instances
- **App Blocks**: Package applications as VHDs for dynamic delivery

## Post-Deployment Configuration

### 0. Verify Service Role

The CDK stack creates a service role for WorkSpaces Applications. Verify it exists:

```bash
# Get the role ARN from stack outputs
aws cloudformation describe-stacks \
  --stack-name WestTekWorkspace \
  --query 'Stacks[0].Outputs[?OutputKey==`WorkSpacesServiceRoleArn`].OutputValue' \
  --output text
```

This role allows WorkSpaces Applications to:
- Access your S3 bucket for home folders
- Create network interfaces in your VPC
- Describe VPC resources

### 1. Create App Block for Browser Application

Since Elastic fleets use app blocks instead of custom images, you need to package your browser application:

#### Option A: Using AWS Console

1. Go to WorkSpaces Applications → App Blocks
2. Click "Create app block"
3. Choose "Create from scratch"
4. Select platform: **Ubuntu Pro 24.04**
5. Upload your application VHD or specify S3 location
6. Configure launch parameters

#### Option B: Using AWS CLI

```bash
# Package Firefox as an app block
aws workspaces create-app-block \
  --name jupyter-browser \
  --description "Firefox browser for Jupyter access" \
  --source-s3-location S3Bucket=your-bucket,S3Key=firefox-app.vhd \
  --setup-script-details ScriptS3Location={S3Bucket=your-bucket,S3Key=setup.sh},ExecutablePath=/usr/bin/firefox
```

### 2. Create Application Resource

```bash
aws workspaces create-application \
  --name "Jupyter Access" \
  --description "Browser for accessing Jupyter environments" \
  --app-block-arn arn:aws:workspaces:region:account:appblock/jupyter-browser \
  --icon-s3-location S3Bucket=your-bucket,S3Key=icon.png \
  --launch-parameters "http://<internal-alb-dns>:80" \
  --platforms UBUNTU_PRO_24_04 \
  --working-directory /tmp
```

### 3. Create Elastic Fleet

```bash
aws workspaces create-fleet \
  --name west-tek-jupyter-fleet \
  --description "Elastic fleet for Jupyter access" \
  --fleet-type ELASTIC \
  --compute-capacity DesiredSessions=1 \
  --platform UBUNTU_PRO_24_04 \
  --instance-type stream.standard.medium \
  --vpc-config SubnetIds=subnet-xxx,subnet-yyy,SecurityGroupIds=sg-zzz \
  --stream-view DESKTOP \
  --max-sessions-per-instance 1 \
  --disconnect-timeout-in-seconds 900 \
  --idle-disconnect-timeout-in-seconds 600 \
  --max-user-duration-in-seconds 28800 \
  --enable-default-internet-access false
```

### 4. Create Stack and Associate Applications

```bash
# Create stack
aws workspaces create-stack \
  --name west-tek-jupyter-stack \
  --description "Stack for Jupyter access" \
  --storage-connectors Type=HOMEFOLDERS,ResourceIdentifier=your-s3-bucket \
  --user-settings Action=CLIPBOARD_COPY_FROM_LOCAL_DEVICE,Permission=ENABLED \
                 Action=CLIPBOARD_COPY_TO_LOCAL_DEVICE,Permission=ENABLED \
                 Action=FILE_UPLOAD,Permission=ENABLED \
                 Action=FILE_DOWNLOAD,Permission=ENABLED

# Associate fleet with stack
aws workspaces associate-fleet \
  --fleet-name west-tek-jupyter-fleet \
  --stack-name west-tek-jupyter-stack

# Associate application with stack
aws workspaces associate-application-to-entitlements \
  --stack-name west-tek-jupyter-stack \
  --application-arn arn:aws:workspaces:region:account:application/jupyter-access
```

### 5. Configure User Access

#### SAML 2.0 Integration (Recommended)

Configure SAML with your identity provider to enable SSO:

```bash
aws workspaces create-stack \
  --name west-tek-jupyter-stack \
  --access-endpoints Type=STREAMING,EndpointType=STREAMING \
  --embed-host-domains your-domain.com
```

#### User Pool

Create users directly:

```bash
aws workspaces create-user \
  --user-name researcher@westtekresearch.com \
  --authentication-type USERPOOL \
  --first-name John \
  --last-name Doe
```

### 6. Generate Streaming URLs

For programmatic access:

```python
import boto3

client = boto3.client('workspaces')

response = client.create_streaming_url(
    StackName='west-tek-jupyter-stack',
    FleetName='west-tek-jupyter-fleet',
    UserId='researcher@westtekresearch.com',
    ApplicationId='jupyter-access',
    Validity=3600  # 1 hour
)

streaming_url = response['StreamingURL']
```

## Packaging Applications for App Blocks

### Creating a VHD with Firefox

1. Launch an Ubuntu Pro 24.04 EC2 instance
2. Install Firefox:
   ```bash
   sudo apt update
   sudo apt install -y firefox
   ```
3. Create VHD:
   ```bash
   # Install tools
   sudo apt install -y qemu-utils
   
   # Create VHD
   qemu-img create -f vpc firefox-app.vhd 10G
   
   # Mount and copy application
   sudo modprobe nbd max_part=8
   sudo qemu-nbd --connect=/dev/nbd0 firefox-app.vhd
   sudo mkfs.ext4 /dev/nbd0
   sudo mount /dev/nbd0 /mnt
   sudo cp -r /usr/bin/firefox /mnt/
   sudo cp -r /usr/lib/firefox /mnt/
   sudo umount /mnt
   sudo qemu-nbd --disconnect /dev/nbd0
   ```
4. Upload to S3:
   ```bash
   aws s3 cp firefox-app.vhd s3://your-bucket/apps/
   ```

## Benefits of Ubuntu Pro 24.04

- **Extended Security Maintenance**: 10 years of security updates
- **Compliance**: FIPS, Common Criteria EAL2
- **Kernel Livepatch**: Apply kernel patches without rebooting
- **25,000+ Packages**: Extended security coverage beyond base OS

## Elastic Fleet Advantages

- **Serverless**: No capacity planning required
- **Cost-Effective**: Pay only for active streaming sessions (minimum 15 minutes)
- **Fast Start**: Applications launch in under 1 minute
- **No Image Management**: AWS manages the base OS image
- **Dynamic Apps**: Applications delivered at runtime from app blocks

## Monitoring

```bash
# Fleet status
aws workspaces describe-fleets --names west-tek-jupyter-fleet

# Active sessions
aws workspaces describe-sessions --stack-name west-tek-jupyter-stack

# CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/WorkSpacesApplications \
  --metric-name ActualCapacity \
  --dimensions Name=Fleet,Value=west-tek-jupyter-fleet \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Average
```

## Troubleshooting

### Applications not launching
- Verify app block VHD is accessible in S3
- Check application launch parameters
- Review CloudWatch logs for errors

### Can't access Jupyter
- Verify internal ALB DNS in launch parameters
- Check security group rules
- Test ALB endpoint from within VPC

### Fleet not available
- Ensure fleet is in RUNNING state
- Check VPC and subnet configuration
- Verify Ubuntu Pro 24.04 is available in your region

## Cost Optimization

- Elastic fleet charges only for active streaming time (minimum 15 minutes)
- No charges when no users are streaming
- Set appropriate session timeouts
- Monitor usage with CloudWatch

## Important Notes

- Ubuntu Pro 24.04 Elastic fleets is a new feature (December 2024)
- CDK/CloudFormation support may be limited initially
- Use AWS Console or CLI for initial setup
- App blocks replace custom image creation for Elastic fleets

