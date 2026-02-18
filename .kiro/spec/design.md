# Design: West Tek Scientific Environment Preservation Platform

## Architecture Overview

The West Tek platform follows a microservices architecture deployed on AWS, designed for scientific environment preservation with enterprise-grade security and compliance. The system uses event-driven architecture to provide real-time drift detection while maintaining complete environment isolation between labs.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      AWS Cloud Infrastructure                      │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │   Web Portal    │  │  WorkSpaces     │  │  Drift Monitor  │    │
│  │   (React/TS)    │  │ Secure Browser  │  │   (Real-time)   │    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘    │
│           │                     │                     │            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │  Auth Service   │  │  API Gateway    │  │ Environment Mgr │    │
│  │  (Cognito/AD)   │  │   (REST API)    │  │  (Container)    │    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘    │
│           │                     │                     │            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │   ECS/Fargate   │  │   EFS Storage   │  │    EventBridge  │    │
│  │ Jupyter Envs    │  │  (Persistent)   │  │   (Events)      │    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘    │
│           │                     │                     │            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │   Document DB   │  │     S3 Storage  │  │   EBS Volumes   │    │
│  │  (MongoDB)      │  │   (Snapshots)   │  │  (Container)    │    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. Web Portal (Frontend)
**Technology**: React 18 with TypeScript, Vite build system
**Styling**: Tailwind CSS with custom West Tek branding
**State Management**: Zustand for client state, React Query for server state

#### Key Components:
- **Environment Dashboard**: Real-time status of all lab environments and Jupyter sessions
- **Snapshot Manager**: Create, view, and restore environment snapshots
- **Drift Monitor**: Live alerts and change detection visualization
- **Collaboration Hub**: Inter-lab environment sharing interface
- **Knowledge Transfer**: Researcher succession and onboarding workflows
- **Jupyter Launcher**: Provision and access Jupyter environments via WorkSpaces Secure Browser

#### Data Flow:
```
User Action → React Component → Zustand State → React Query → API Gateway → Microservice
```

### 2. Research Environment Access Layer
**Technology**: Amazon WorkSpaces Secure Browser with ECS/Fargate backend
**Applications**: Jupyter Notebook Server running in containers
**Access Pattern**: Browser-based secure access to containerized research environments

#### Architecture Flow:
```
Researcher → WorkSpaces Secure Browser → ALB → ECS/Fargate Task → Jupyter Container
                                                        ↓
                                            EFS Mount: /home/researcher/notebooks
                                            EBS Volume: /opt/jupyter (configs/kernels)
```

#### Container Management:
- **Dynamic Provisioning**: Spin up Jupyter containers on-demand per researcher
- **Environment Isolation**: Each researcher gets dedicated ECS task with isolated resources
- **Session Persistence**: Jupyter state maintained across browser sessions
- **Auto-scaling**: ECS manages container lifecycle based on usage

### 3. API Gateway (Backend Entry Point)
**Technology**: AWS API Gateway with Lambda proxy integration
**Authentication**: JWT tokens from Cognito integrated with West Tek AD
**Rate Limiting**: Per-lab quotas to prevent resource abuse

#### Endpoints:
```
GET  /api/environments           - List lab environments
POST /api/environments/jupyter   - Launch Jupyter environment
POST /api/environments/snapshot  - Create environment snapshot  
GET  /api/environments/{id}/drift - Get drift analysis
POST /api/collaboration/share    - Share environment with other lab
GET  /api/knowledge/transfer     - Get transfer package
```

### 4. Environment Manager (Core Service)
**Technology**: Python 3.11 with FastAPI, running on ECS Fargate
**Database**: DocumentDB (MongoDB-compatible) for flexible schema
**Caching**: ElastiCache Redis for performance
**Container Orchestration**: ECS with Fargate for Jupyter environments

#### Core Functions:
- **Container Lifecycle Management**: Provision, monitor, and terminate Jupyter containers
- **Environment Discovery**: Automated scanning of lab systems and running containers
- **State Management**: Track environment configurations and changes
- **Access Control**: Lab-based isolation with role-based permissions
- **Audit Logging**: Complete change tracking for compliance
- **EFS Mount Management**: Dynamic provisioning of researcher storage

#### Data Models:
```python
Environment {
    id: UUID
    lab_id: string
    researcher_id: string
    name: string
    created_at: datetime
    last_snapshot: datetime
    drift_status: enum [STABLE, MINOR_DRIFT, CRITICAL_DRIFT]
    configuration_hash: string
    container_info: {
        task_arn: string
        cluster_name: string
        jupyter_url: string
        efs_access_point: string
        ebs_volume_id: string
    }
    metadata: {
        experiment_id: string
        funding_source: string
        criticality: enum
        jupyter_packages: array
    }
}

Snapshot {
    id: UUID
    environment_id: UUID
    created_by: string
    timestamp: datetime
    s3_location: string
    size_bytes: integer
    checksum: string
    container_image: string
    efs_snapshot_id: string
    ebs_snapshot_id: string
    metadata: {
        jupyter_version: string
        installed_packages: array
        notebook_count: integer
        configuration_files: array
        notes: string
    }
}
```

### 5. Drift Detection System
**Technology**: Python with AWS Lambda functions triggered by EventBridge
**Monitoring**: CloudWatch custom metrics and alarms
**Storage**: DynamoDB for high-performance change tracking
**Container Monitoring**: ECS task monitoring and container introspection

#### Detection Methods:
- **Container State Monitoring**: Track ECS task configuration and resource changes
- **Jupyter Environment Tracking**: Monitor installed packages, kernels, and extensions
- **EFS File System Monitoring**: Track changes to notebook files and data
- **EBS Volume Changes**: Monitor container filesystem modifications
- **Network Configuration**: Monitor container networking and security group changes
- **Package Drift**: Compare Jupyter package versions against baseline snapshots

#### Alert System:
```
Container Change → EventBridge → Lambda Function → Severity Analysis → 
SES Email + SNS SMS + Dashboard Update → Audit Log
```

#### Jupyter-Specific Monitoring:
- **Package Installation**: Detect when researchers install new Python packages
- **Kernel Changes**: Monitor addition/modification of Jupyter kernels
- **Extension Updates**: Track Jupyter Lab/Notebook extension changes
- **Configuration Drift**: Monitor jupyter_config.py and related files
- **Data File Changes**: Track modifications to research datasets and notebooks

### 6. Snapshot Engine
**Technology**: Docker containers on ECS with custom snapshot tools
**Storage**: S3 with versioning and cross-region replication for container images
**Persistent Storage**: EFS snapshots for notebooks, EBS snapshots for container state
**Compression**: Custom algorithm optimized for Jupyter environments

#### Snapshot Process:
1. **Pre-Snapshot Validation**: Verify Jupyter container and EFS mount stability
2. **Container Image Capture**: Create immutable Docker image of Jupyter environment
3. **EFS Snapshot**: Point-in-time snapshot of researcher's notebook directory
4. **EBS Snapshot**: Capture container filesystem state and configurations
5. **Metadata Generation**: Extract Jupyter package list, kernel info, notebook inventory
6. **Compression and Storage**: Optimized storage in S3 with deduplication
7. **Verification**: Post-snapshot integrity checking and restoration testing

#### Restoration Process:
1. **Environment Provisioning**: Create new ECS task with restored container image
2. **Storage Restoration**: Mount restored EFS snapshot and attach EBS volume
3. **Jupyter Configuration**: Restore Jupyter server settings and custom kernels
4. **Access Setup**: Configure WorkSpaces Secure Browser access to new container
5. **Validation**: Verify all notebooks and packages are accessible
6. **Handoff**: Provide researcher with secure browser link to restored environment

#### Storage Optimization:
- **Container Layer Caching**: Reuse common base layers across snapshots
- **EFS Deduplication**: Built-in deduplication for notebook files
- **Incremental EBS**: Only snapshot changed blocks for efficiency
- **Intelligent Tiering**: Automatic movement to cost-effective storage classes

---

## Data Architecture

### Primary Data Stores

#### 1. DocumentDB Cluster
**Purpose**: Environment metadata, user data, audit logs
**Configuration**: 3-node replica set with cross-AZ deployment
**Backup**: Automated daily backups with 30-day retention

#### 2. Amazon EFS (Elastic File System)
**Purpose**: Persistent storage for Jupyter notebooks and research data
**Configuration**: General Purpose performance mode with Intelligent Tiering
**Access Control**: EFS Access Points per researcher with POSIX permissions
**Mount Structure**:
- `/home/{researcher_id}/notebooks` - Personal Jupyter notebooks
- `/shared/{lab_id}/datasets` - Shared lab datasets  
- `/shared/{lab_id}/libraries` - Common research libraries

#### 3. EBS Volumes (Elastic Block Store)
**Purpose**: Container-specific persistent storage
**Configuration**: gp3 volumes with encryption at rest
**Usage Pattern**:
- Jupyter server configuration and custom kernels
- Installed Python packages and virtual environments
- Container operating system modifications
- Temporary computation scratch space

#### 4. S3 Storage Classes
**Hot Storage**: Container images and recent snapshots (30 days) - S3 Standard
**Warm Storage**: Older snapshots (1 year) - S3 Standard-IA  
**Cold Storage**: Archive snapshots (10+ years) - S3 Glacier Deep Archive
**Container Registry**: ECR for base Jupyter images and custom builds

#### 5. DynamoDB Tables
**Purpose**: High-performance drift detection and real-time alerts
**Configuration**: On-demand billing with Global Secondary Indexes
**Data Types**: Container state changes, package modifications, file system events

### Container Storage Architecture
```
ECS/Fargate Task
├── Container Image (ECR) - Immutable Jupyter environment
├── EBS Volume - /opt/jupyter (configs, kernels, packages)  
├── EFS Mount - /home/researcher (notebooks, data)
└── Ephemeral Storage - /tmp (temporary computation)
```

### Snapshot Architecture
```
Complete Environment Snapshot
├── Container Image → S3 (Docker layers)
├── EFS Snapshot → AWS EFS Backups
├── EBS Snapshot → AWS EBS Snapshots
└── Metadata → DocumentDB (package lists, config hashes)
```

### Data Security
- **Encryption**: AES-256 encryption at rest, TLS 1.3 in transit
- **Access Control**: IAM roles with lab-based resource isolation
- **Backup**: Cross-region backup with 99.999999999% durability
- **Compliance**: SOC 2 Type II, ISO 27001, HIPAA-ready architecture

---

## Security Design

### Network Architecture
```
Internet → CloudFront → ALB → Private Subnets → ECS/Lambda
                         ↓
                    NAT Gateway → Internet (outbound only)
```

### Authentication & Authorization
- **Primary**: AWS Cognito User Pool integrated with West Tek AD
- **Lab Isolation**: Each lab operates in logical isolation with dedicated IAM roles
- **API Security**: JWT tokens with short expiration and refresh mechanism
- **Audit Trail**: CloudTrail logging of all administrative actions

### Data Protection
- **Environment Snapshots**: Client-side encryption before S3 upload
- **PII Handling**: Automated detection and redaction of personal data
- **Cross-Lab Access**: Zero-trust model with explicit sharing permissions
- **Backup Encryption**: Separate encryption keys managed by AWS KMS

---

## Integration Points

### West Tek Active Directory
- **SSO Integration**: SAML 2.0 federation with Cognito
- **Group Mapping**: AD security groups mapped to application roles
- **Provisioning**: Automated account creation for new researchers

### Lab Infrastructure
- **Agent Deployment**: Lightweight agents on lab workstations and servers
- **Network Access**: VPN or AWS Direct Connect for secure communication
- **Legacy Systems**: API adapters for older lab management systems

### External Systems
- **Funding Systems**: API integration for automatic experiment-funding mapping
- **Compliance Tools**: Export capabilities for regulatory reporting
- **Notification Systems**: Integration with lab's existing alert mechanisms

---

## Deployment Architecture

### AWS Services Used
- **Compute**: ECS Fargate (Jupyter containers), Lambda (drift detection, API functions)
- **Storage**: S3 (snapshots, container images), EFS (persistent notebooks), EBS (container state), DocumentDB (metadata), DynamoDB (real-time data), ElastiCache (caching)
- **Container**: ECR (Docker registry), ECS (orchestration)
- **End User Computing**: WorkSpaces Secure Browser (research environment access)
- **Networking**: VPC, ALB, CloudFront, API Gateway, NAT Gateway
- **Security**: Cognito (authentication), IAM (authorization), KMS (encryption), Certificate Manager (SSL/TLS)
- **Monitoring**: CloudWatch (metrics/logs), X-Ray (tracing), EventBridge (events)
- **Backup**: AWS Backup (EFS/EBS), Cross-Region Replication (S3)

### Infrastructure as Code
- **Primary**: AWS CDK with TypeScript
- **Configuration**: Parameter Store for environment-specific settings
- **Secrets**: AWS Secrets Manager for database credentials and API keys
- **Deployment**: GitHub Actions with AWS CodeDeploy

### Multi-Environment Strategy
- **Development**: Single-AZ deployment with reduced redundancy
- **Staging**: Production-like environment for testing
- **Production**: Multi-AZ, auto-scaling, full backup and monitoring

---

## Performance Design

### Scalability Targets
- **Concurrent Users**: 500 researchers across 50 labs
- **Snapshot Operations**: 100 concurrent snapshot creations
- **Drift Monitoring**: Real-time monitoring of 1000+ environments
- **Data Growth**: 10TB of snapshot data growth per year

### Performance Optimizations
- **Caching Strategy**: Multi-level caching with Redis and CloudFront
- **Database Optimization**: Read replicas and connection pooling
- **Async Processing**: Background jobs for heavy operations
- **CDN**: Global content delivery for web assets and documentation

### Monitoring and Alerting
- **SLA Targets**: 99.9% uptime, <3s response time, <15min snapshot restoration
- **Custom Metrics**: Business-specific KPIs tracked in CloudWatch
- **Alerting**: Multi-channel alerting for different severity levels
- **Dashboards**: Real-time operational dashboards for IT teams

---

## Disaster Recovery

### Backup Strategy
- **RTO**: 4 hours for complete system recovery
- **RPO**: 15 minutes maximum data loss
- **Cross-Region**: Automated replication to secondary AWS region
- **Testing**: Monthly DR testing with documented procedures

### Recovery Procedures
1. **Database Recovery**: DocumentDB point-in-time recovery
2. **Application Recovery**: Blue-green deployment from backup region
3. **Data Recovery**: S3 cross-region replication with versioning
4. **Network Recovery**: Route 53 health checks with automatic failover