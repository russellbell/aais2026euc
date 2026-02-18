from aws_cdk import (
    Stack,
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_efs as efs,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_logs as logs,
    aws_cognito as cognito,
    aws_elasticloadbalancingv2 as elbv2,
    Duration,
    CfnOutput,
)
from constructs import Construct


class ComputeStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: ec2.Vpc,
        efs_file_system: efs.FileSystem,
        jupyter_ecr_repo: ecr.Repository,
        api_ecr_repo: ecr.Repository,
        user_pool: cognito.UserPool,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Security group for ECS tasks
        self.ecs_security_group = ec2.SecurityGroup(
            self, "ECSTaskSecurityGroup",
            vpc=vpc,
            description="Security group for ECS tasks",
            allow_all_outbound=True
        )

        # Security group for ALB
        self.alb_security_group = ec2.SecurityGroup(
            self, "ALBSecurityGroup",
            vpc=vpc,
            description="Security group for Application Load Balancer",
            allow_all_outbound=True
        )

        # Allow HTTP traffic to ALB from within VPC only
        self.alb_security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(80),
            description="Allow HTTP from VPC"
        )

        # Allow ALB to reach ECS tasks
        self.ecs_security_group.add_ingress_rule(
            peer=self.alb_security_group,
            connection=ec2.Port.tcp(8000),
            description="Allow traffic from ALB"
        )

        # ECS Cluster
        self.cluster = ecs.Cluster(
            self, "WestTekCluster",
            vpc=vpc,
            container_insights=True
        )

        # Task execution role
        task_execution_role = iam.Role(
            self, "TaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy"
                )
            ]
        )

        # Grant ECR access
        jupyter_ecr_repo.grant_pull(task_execution_role)
        api_ecr_repo.grant_pull(task_execution_role)

        # Task role for API service
        api_task_role = iam.Role(
            self, "APITaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com")
        )

        # API Task Definition
        self.api_task_definition = ecs.FargateTaskDefinition(
            self, "APITaskDefinition",
            memory_limit_mib=2048,
            cpu=1024,
            execution_role=task_execution_role,
            task_role=api_task_role
        )

        # API Container (placeholder - will be built separately)
        api_container = self.api_task_definition.add_container(
            "APIContainer",
            image=ecs.ContainerImage.from_registry("public.ecr.aws/docker/library/python:3.11-slim"),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="api",
                log_retention=logs.RetentionDays.ONE_WEEK
            ),
            environment={
                "ENVIRONMENT": "production"
            },
            # Placeholder command to keep container running
            command=["python3", "-m", "http.server", "8000"],
            essential=True
        )

        api_container.add_port_mappings(
            ecs.PortMapping(container_port=8000, protocol=ecs.Protocol.TCP)
        )

        # Application Load Balancer for API (internal)
        self.api_alb = elbv2.ApplicationLoadBalancer(
            self, "APIALB",
            vpc=vpc,
            internet_facing=False,
            security_group=self.alb_security_group,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)
        )

        # API Service
        self.api_service = ecs.FargateService(
            self, "APIService",
            cluster=self.cluster,
            task_definition=self.api_task_definition,
            desired_count=1,  # Start with 1 for testing
            assign_public_ip=False,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[self.ecs_security_group]
        )

        # Target group and listener
        api_target_group = elbv2.ApplicationTargetGroup(
            self, "APITargetGroup",
            vpc=vpc,
            port=8000,
            protocol=elbv2.ApplicationProtocol.HTTP,
            target_type=elbv2.TargetType.IP,
            health_check=elbv2.HealthCheck(
                path="/",
                interval=Duration.seconds(60),
                timeout=Duration.seconds(30),
                healthy_threshold_count=2,
                unhealthy_threshold_count=3
            ),
            deregistration_delay=Duration.seconds(30)
        )

        self.api_service.attach_to_application_target_group(api_target_group)

        self.api_alb.add_listener(
            "APIListener",
            port=80,
            default_target_groups=[api_target_group]
        )

        # Jupyter Task Definition (template for dynamic tasks)
        jupyter_task_role = iam.Role(
            self, "JupyterTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com")
        )

        self.jupyter_task_definition = ecs.FargateTaskDefinition(
            self, "JupyterTaskDefinition",
            memory_limit_mib=4096,
            cpu=2048,
            execution_role=task_execution_role,
            task_role=jupyter_task_role
        )

        # Add EFS volume to Jupyter task
        self.jupyter_task_definition.add_volume(
            name="notebook-storage",
            efs_volume_configuration=ecs.EfsVolumeConfiguration(
                file_system_id=efs_file_system.file_system_id
            )
        )

        # Jupyter Container (placeholder)
        jupyter_container = self.jupyter_task_definition.add_container(
            "JupyterContainer",
            image=ecs.ContainerImage.from_registry("jupyter/scipy-notebook:latest"),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="jupyter",
                log_retention=logs.RetentionDays.ONE_WEEK
            ),
            environment={
                "JUPYTER_ENABLE_LAB": "yes"
            },
            essential=True
        )

        jupyter_container.add_port_mappings(
            ecs.PortMapping(container_port=8888, protocol=ecs.Protocol.TCP)
        )

        jupyter_container.add_mount_points(
            ecs.MountPoint(
                source_volume="notebook-storage",
                container_path="/home/jovyan/work",
                read_only=False
            )
        )

        CfnOutput(self, "ClusterName", value=self.cluster.cluster_name)
        CfnOutput(self, "APILoadBalancerDNS", value=self.api_alb.load_balancer_dns_name)
        CfnOutput(self, "JupyterTaskDefinitionArn", value=self.jupyter_task_definition.task_definition_arn)
