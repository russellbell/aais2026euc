# ECS Troubleshooting Guide

## Common ECS Issues and Fixes

### 1. Tasks Not Starting

Check CloudWatch Logs:
```bash
aws logs tail /aws/ecs/api --follow
```

Common causes:
- Container image not found (check ECR repository)
- Insufficient IAM permissions
- Security group blocking traffic
- Container command failing

### 2. Health Check Failures

The API service health check is set to `/` (root path). If your container doesn't respond on this path, tasks will be marked unhealthy.

Check target group health:
```bash
aws elbv2 describe-target-health \
  --target-group-arn <target-group-arn>
```

### 3. Security Group Issues

Verify security group rules:
- ALB security group: Allow inbound port 80 from 0.0.0.0/0
- ECS task security group: Allow inbound port 8000 from ALB security group
- EFS security group: Allow inbound port 2049 from ECS task security group

### 4. Service Not Reaching Desired Count

Check service events:
```bash
aws ecs describe-services \
  --cluster <cluster-name> \
  --services APIService
```

Look for error messages in the events section.

### 5. Container Logs

View container logs directly:
```bash
# Get task ARN
aws ecs list-tasks --cluster <cluster-name> --service-name APIService

# View logs for specific task
aws ecs describe-tasks --cluster <cluster-name> --tasks <task-arn>
```

## Quick Fixes Applied

1. Added explicit security groups for ALB and ECS tasks
2. Configured ALB → ECS task security group rules
3. Added placeholder command to API container (python http.server)
4. Changed health check path from `/health` to `/` for placeholder
5. Increased health check intervals and timeouts
6. Reduced initial desired count to 1 for testing
7. Added `essential=True` to containers
8. Connected EFS security group properly

## Testing the Deployment

After deploying, test the ALB endpoint:
```bash
# Get ALB DNS
aws cloudformation describe-stacks \
  --stack-name WestTekCompute \
  --query 'Stacks[0].Outputs[?OutputKey==`APILoadBalancerDNS`].OutputValue' \
  --output text

# Test endpoint
curl http://<alb-dns>/
```

You should see a directory listing from the Python http.server.

## Next Steps

Once the infrastructure is stable:
1. Build and push actual API container to ECR
2. Update task definition to use your API image
3. Change health check path to `/health` or your API's health endpoint
4. Increase desired count for production
