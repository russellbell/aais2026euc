#!/usr/bin/env python3
import aws_cdk as cdk
from infrastructure.network_stack import NetworkStack
from infrastructure.storage_stack import StorageStack
from infrastructure.compute_stack import ComputeStack
from infrastructure.auth_stack import AuthStack
from infrastructure.workspace_stack import WorkspaceStack

app = cdk.App()

env = cdk.Environment(
    account=app.node.try_get_context("account"),
    region=app.node.try_get_context("region") or "us-east-1"
)

# Network foundation
network_stack = NetworkStack(app, "WestTekNetwork", env=env)

# Storage layer
storage_stack = StorageStack(
    app, "WestTekStorage",
    vpc=network_stack.vpc,
    efs_security_group=network_stack.efs_security_group,
    env=env
)

# Authentication
auth_stack = AuthStack(app, "WestTekAuth", env=env)

# Compute layer
compute_stack = ComputeStack(
    app, "WestTekCompute",
    vpc=network_stack.vpc,
    efs_file_system=storage_stack.efs_file_system,
    jupyter_ecr_repo=storage_stack.jupyter_ecr_repo,
    api_ecr_repo=storage_stack.api_ecr_repo,
    user_pool=auth_stack.user_pool,
    env=env
)

# Workspace access layer
workspace_stack = WorkspaceStack(
    app, "WestTekWorkspace",
    vpc=network_stack.vpc,
    env=env
)

app.synth()
