from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_ecr as ecr,
    aws_efs as efs,
    aws_ec2 as ec2,
    aws_dynamodb as dynamodb,
    RemovalPolicy,
    CfnOutput,
)
from constructs import Construct


class StorageStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: ec2.Vpc,
        efs_security_group: ec2.SecurityGroup,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 bucket for environment snapshots
        self.snapshots_bucket = s3.Bucket(
            self, "SnapshotsBucket",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN
        )

        # S3 bucket for frontend hosting
        self.frontend_bucket = s3.Bucket(
            self, "FrontendBucket",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY
        )

        # ECR repository for Jupyter container images
        self.jupyter_ecr_repo = ecr.Repository(
            self, "JupyterRepository",
            image_scan_on_push=True,
            removal_policy=RemovalPolicy.RETAIN
        )

        # ECR repository for API container images
        self.api_ecr_repo = ecr.Repository(
            self, "APIRepository",
            image_scan_on_push=True,
            removal_policy=RemovalPolicy.RETAIN
        )

        # EFS for persistent notebook storage
        self.efs_file_system = efs.FileSystem(
            self, "NotebookStorage",
            vpc=vpc,
            encrypted=True,
            performance_mode=efs.PerformanceMode.GENERAL_PURPOSE,
            throughput_mode=efs.ThroughputMode.BURSTING,
            security_group=efs_security_group,
            removal_policy=RemovalPolicy.RETAIN
        )

        # DynamoDB table for drift tracking
        self.drift_table = dynamodb.Table(
            self, "DriftTrackingTable",
            partition_key=dynamodb.Attribute(
                name="environment_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN
        )

        # DynamoDB table for environment metadata
        self.metadata_table = dynamodb.Table(
            self, "EnvironmentMetadataTable",
            partition_key=dynamodb.Attribute(
                name="environment_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN
        )

        CfnOutput(self, "SnapshotsBucketName", value=self.snapshots_bucket.bucket_name)
        CfnOutput(self, "JupyterECRRepoUri", value=self.jupyter_ecr_repo.repository_uri)
        CfnOutput(self, "APIECRRepoUri", value=self.api_ecr_repo.repository_uri)
        CfnOutput(self, "EFSFileSystemId", value=self.efs_file_system.file_system_id)
