from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_s3 as s3,
    aws_workspacesthinclient as workspaces_thin_client,
    CfnOutput,
    RemovalPolicy,
    CustomResource,
    custom_resources as cr,
)
from constructs import Construct


class WorkspaceStack(Stack):
    """
    WorkSpaces Application stack for streaming Jupyter environments.
    Note: WorkSpaces Applications with Ubuntu Pro 24.04 Elastic fleets is a new feature.
    CDK L2 constructs may not be available yet, so we use L1 (Cfn) constructs.
    """
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: ec2.Vpc,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Service role for AppStream 2.0 (AmazonAppStreamServiceAccess)
        # This is automatically created when you first use AppStream in the console,
        # but we need to create it explicitly for infrastructure-as-code
        self.appstream_service_role = iam.Role(
            self, "AppStreamServiceAccess",
            role_name="AmazonAppStreamServiceAccess",
            path="/service-role/",
            assumed_by=iam.ServicePrincipal("appstream.amazonaws.com"),
            description="Service role for AppStream 2.0 to access AWS resources",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonAppStreamServiceAccess")
            ]
        )

        # Service-linked role for Application Auto Scaling
        # This is created automatically by AWS when needed, but we can create it explicitly
        # Note: Service-linked roles have specific naming and can only be created once per account
        self.create_autoscaling_service_linked_role = cr.AwsCustomResource(
            self, "CreateAutoScalingServiceLinkedRole",
            on_create=cr.AwsSdkCall(
                service="IAM",
                action="createServiceLinkedRole",
                parameters={
                    "AWSServiceName": "appstream.application-autoscaling.amazonaws.com",
                    "Description": "Service-linked role for Application Auto Scaling for AppStream fleets"
                },
                physical_resource_id=cr.PhysicalResourceId.of("AppStreamAutoScalingServiceLinkedRole"),
                ignore_error_codes_matching="InvalidInput"  # Ignore if already exists
            ),
            policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE
            )
        )

        # Service-linked role for WorkSpaces Applications (formerly AppStream 2.0)
        # This role allows WorkSpaces Applications to access AWS resources on your behalf
        self.workspaces_service_role = iam.Role(
            self, "WorkSpacesApplicationsServiceRole",
            assumed_by=iam.ServicePrincipal("appstream.amazonaws.com"),
            description="Service role for WorkSpaces Applications to access AWS resources",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3ReadOnlyAccess")
            ]
        )

        # Add inline policy for additional permissions
        self.workspaces_service_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ec2:DescribeVpcs",
                    "ec2:DescribeSubnets",
                    "ec2:DescribeSecurityGroups",
                    "ec2:DescribeNetworkInterfaces",
                    "ec2:CreateNetworkInterface",
                    "ec2:DeleteNetworkInterface",
                    "ec2:DescribeAvailabilityZones"
                ],
                resources=["*"]
            )
        )

        # S3 bucket for WorkSpaces Application settings and home folders
        self.workspaces_bucket = s3.Bucket(
            self, "WorkSpacesBucket",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN
        )

        # Grant WorkSpaces service role access to the bucket
        self.workspaces_bucket.grant_read_write(self.workspaces_service_role)

        # Security group for WorkSpaces Application instances
        self.workspaces_security_group = ec2.SecurityGroup(
            self, "WorkSpacesSecurityGroup",
            vpc=vpc,
            description="Security group for WorkSpaces Application instances",
            allow_all_outbound=True
        )

        # Allow WorkSpaces to access internal ALB
        self.workspaces_security_group.add_egress_rule(
            peer=ec2.Peer.ipv4(vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(80),
            description="Allow access to internal ALB"
        )

        # Note: As of now, WorkSpaces Applications with Ubuntu Pro 24.04 Elastic fleets
        # may need to be configured via AWS Console or CLI as CDK support is limited.
        # This is a placeholder for when full CDK support becomes available.
        
        CfnOutput(self, "AppStreamServiceRoleArn", value=self.appstream_service_role.role_arn)
        CfnOutput(self, "WorkSpacesBucketName", value=self.workspaces_bucket.bucket_name)
        CfnOutput(
            self, "WorkSpacesServiceRoleArn",
            value=self.workspaces_service_role.role_arn,
            description="IAM role ARN for WorkSpaces Applications service"
        )
        CfnOutput(
            self, "WorkSpacesSetupInstructions",
            value="Configure WorkSpaces Applications Elastic fleet with Ubuntu Pro 24.04 via AWS Console"
        )
        CfnOutput(
            self, "WorkSpacesSecurityGroupId",
            value=self.workspaces_security_group.security_group_id
        )

