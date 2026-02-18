from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    CfnOutput,
)
from constructs import Construct


class NetworkStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # VPC with public and private subnets across 2 AZs
        self.vpc = ec2.Vpc(
            self, "WestTekVPC",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Isolated",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24
                )
            ]
        )

        # Security group for ECS tasks
        self.ecs_security_group = ec2.SecurityGroup(
            self, "ECSSecurityGroup",
            vpc=self.vpc,
            description="Security group for ECS tasks",
            allow_all_outbound=True
        )

        # Security group for EFS
        self.efs_security_group = ec2.SecurityGroup(
            self, "EFSSecurityGroup",
            vpc=self.vpc,
            description="Security group for EFS",
            allow_all_outbound=False
        )

        # Allow ECS tasks to access EFS
        self.efs_security_group.add_ingress_rule(
            peer=self.ecs_security_group,
            connection=ec2.Port.tcp(2049),
            description="Allow NFS from ECS tasks"
        )

        # Security group for DocumentDB
        self.docdb_security_group = ec2.SecurityGroup(
            self, "DocumentDBSecurityGroup",
            vpc=self.vpc,
            description="Security group for DocumentDB",
            allow_all_outbound=False
        )

        # Allow ECS tasks to access DocumentDB
        self.docdb_security_group.add_ingress_rule(
            peer=self.ecs_security_group,
            connection=ec2.Port.tcp(27017),
            description="Allow MongoDB from ECS tasks"
        )

        CfnOutput(self, "VPCId", value=self.vpc.vpc_id)
