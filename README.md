# West Tek Scientific Environment Preservation Platform

A platform for preserving exact Jupyter-based scientific computing environments across decades while enabling controlled collaboration between research labs.

## 🏗️ Architecture

Our platform leverages AWS's container orchestration and end-user computing services to provide scientists with reproducible, drift-resistant research environments:

![West Tek AWS Architecture Diagram](west-tek-architecture.svg)

## Overview

West Tek Research requires a system that guarantees experimental reproducibility by capturing complete Jupyter environment snapshots, detecting environmental drift in real-time, and enabling secure knowledge transfer between researchers. The platform provides containerized Jupyter environments with persistent storage, ensuring research continuity and compliance while reducing IT overhead.

## Key Features

- **Jupyter Environment Management**: Launch and access containerized Jupyter notebook servers with secure browser-based access via WorkSpaces Secure Browser
- **Environment Snapshot Management**: Create and restore complete Jupyter environment snapshots including container images, Python packages, notebooks, and data with 100% fidelity
- **Real-time Drift Detection**: Immediate alerts when Python packages, Jupyter kernels, or configurations change unexpectedly
- **Lab Collaboration Gateway**: Controlled sharing of Jupyter environments between labs with audit trails and read-only templates
- **Knowledge Transfer Pipeline**: Seamless researcher succession with complete experimental context including notebooks, packages, and execution history
- **Compliance & Audit Trail**: Complete audit trails for research reproducibility and funding reviews

## Architecture

Built on AWS infrastructure using:
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS
- **Backend**: FastAPI (Python 3.11) on ECS Fargate
- **Research Environments**: Jupyter Notebook containers on ECS/Fargate with WorkSpaces Secure Browser access
- **Storage**: 
  - S3 (container image snapshots)
  - ECR (Docker registry for Jupyter images)
  - EFS (persistent notebook storage)
  - EBS (container state and packages)
  - DocumentDB (metadata)
  - DynamoDB (drift tracking)
- **Security**: AWS Cognito with Active Directory integration, IAM roles, KMS encryption
- **Monitoring**: CloudWatch, EventBridge, X-Ray

## Container Architecture

Each researcher gets an isolated Jupyter environment:
```
ECS/Fargate Task
├── Container Image (ECR) - Immutable Jupyter environment
├── EBS Volume - /opt/jupyter (configs, kernels, packages)  
├── EFS Mount - /home/researcher (notebooks, data)
└── Ephemeral Storage - /tmp (temporary computation)
```

Access via WorkSpaces Secure Browser provides secure, browser-based access to Jupyter environments without local software installation.

## Project Structure

```
.kiro/
  spec/
    requirements.md  # User stories and acceptance criteria
    design.md        # Architecture and technical design
    task.md          # Development phases and tasks
```

## Development Phases

1. **Phase 1**: Foundation & Core Infrastructure (AWS CDK, ECS/Fargate, Auth, API, EFS/EBS)
2. **Phase 2**: Frontend & User Experience (React dashboard, Jupyter launcher, snapshot UI)
3. **Phase 3**: Core Platform Features (Jupyter container engine, snapshot/restore, drift detection, knowledge transfer)
4. **Phase 4**: Advanced Features (Inter-lab collaboration, analytics, enhanced drift detection)
5. **Phase 5**: Production Readiness (Security, performance, monitoring)

## Success Criteria

- 100% accurate Jupyter environment recreation with identical package versions after 6+ months
- Zero research invalidation incidents due to unexpected package or configuration changes
- 75% reduction in time to share and align Jupyter environments between labs
- New researchers productive in inherited Jupyter environments within 1 week instead of 4 weeks
- 60% reduction in IT support tickets for environment and package management issues
- <5 minute Jupyter container provisioning time
- <15 minute environment restore time including container and storage

## Getting Started

Documentation for setup and deployment will be added as development progresses.

## License

Proprietary - West Tek Research
