# Design: West Tek Scientific Environment Preservation Platform

## Architecture Overview

The West Tek platform follows a microservices architecture deployed on AWS, designed for scientific environment preservation with enterprise-grade security and compliance. The system uses event-driven architecture to provide real-time drift detection while maintaining complete environment isolation between labs.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     AWS Cloud Infrastructure                    │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Web Portal    │  │  API Gateway    │  │  Drift Monitor  │  │
│  │   (React/TS)    │  │   (REST API)    │  │   (Real-time)   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│           │                     │                     │          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  Auth Service   │  │ Environment Mgr │  │ Snapshot Engine │  │
│  │  (Cognito/AD)   │  │  (Container)    │  │   (ECS Tasks)   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│           │                     │                     │          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Document DB   │  │     S3 Storage  │  │    EventBridge  │  │
│  │  (MongoDB)      │  │   (Snapshots)   │  │   (Events)      │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. Web Portal (Frontend)
**Technology**: React 18 with TypeScript, Vite build system
**Styling**: Tailwind CSS with custom West Tek branding
**State Management**: Zustand for client state, React Query for server state

#### Key Components:
- **Environment Dashboard**: Real-time status of all lab environments
- **Snapshot Manager**: Create, view, and restore environment snapshots
- **Drift Monitor**: Live alerts and change detection visualization
- **Collaboration Hub**: Inter-lab environment sharing interface
- **Knowledge Transfer**: Researcher succession and onboarding workflows

#### Data Flow:
```
User Action → React Component → Zustand State → React Query → API Gateway → Microservice
```

### 2. API Gateway (Backend Entry Point)
**Technology**: AWS API Gateway with Lambda proxy integration
**Authentication**: JWT tokens from Cognito integrated with West Tek AD
**Rate Limiting**: Per-lab quotas to prevent resource abuse

#### Endpoints:
```
GET  /api/environments           - List lab environments
POST /api/environments/snapshot  - Create environment snapshot
GET  /api/environments/{id}/drift - Get drift analysis
POST /api/collaboration/share    - Share environment with other lab
GET  /api/knowledge/transfer     - Get transfer package
```

### 3. Environment Manager (Core Service)
**Technology**: Python 3.11 with FastAPI, running on ECS Fargate
**Database**: DocumentDB (MongoDB-compatible) for flexible schema
**Caching**: ElastiCache Redis for performance

#### Core Functions:
- **Environment Discovery**: Automated scanning of lab systems
- **State Management**: Track environment configurations and changes
- **Access Control**: Lab-based isolation with role-based permissions
- **Audit Logging**: Complete change tracking for compliance

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
    metadata: {
        experiment_id: string
        funding_source: string
        criticality: enum
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
    metadata: {
        os_version: string
        installed_packages: array
        configuration_files: array
        notes: string
    }
}
```

### 4. Drift Detection System
**Technology**: Python with AWS Lambda functions triggered by EventBridge
**Monitoring**: CloudWatch custom metrics and alarms
**Storage**: DynamoDB for high-performance change tracking

#### Detection Methods:
- **File System Monitoring**: AWS Inspector for OS-level changes
- **Package Tracking**: Compare installed software against baseline
- **Configuration Drift**: Deep comparison of config files and registry settings
- **Network Changes**: Monitor network configurations and connectivity

#### Alert System:
```
Change Detected → Lambda Function → Severity Analysis → 
SES Email + SNS SMS + Dashboard Update → Audit Log
```

### 5. Snapshot Engine
**Technology**: Docker containers on ECS with custom snapshot tools
**Storage**: S3 with versioning and cross-region replication
**Compression**: Custom algorithm optimized for scientific environments

#### Snapshot Process:
1. **Pre-Snapshot Validation**: Verify environment stability
2. **System State Capture**: OS, applications, configurations, data
3. **Incremental Analysis**: Delta comparison with previous snapshots
4. **Compression and Storage**: Optimized storage in S3
5. **Metadata Generation**: Searchable tags and documentation
6. **Verification**: Post-snapshot integrity checking

---

## Data Architecture

### Primary Data Stores

#### 1. DocumentDB Cluster
**Purpose**: Environment metadata, user data, audit logs
**Configuration**: 3-node replica set with cross-AZ deployment
**Backup**: Automated daily backups with 30-day retention

#### 2. S3 Storage Classes
**Hot Storage**: Recent snapshots (30 days) - S3 Standard
**Warm Storage**: Older snapshots (1 year) - S3 Standard-IA  
**Cold Storage**: Archive snapshots (10+ years) - S3 Glacier Deep Archive

#### 3. DynamoDB Tables
**Purpose**: High-performance drift detection and real-time alerts
**Configuration**: On-demand billing with Global Secondary Indexes

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
- **Compute**: ECS Fargate, Lambda
- **Storage**: S3, DocumentDB, DynamoDB, ElastiCache
- **Networking**: VPC, ALB, CloudFront, API Gateway
- **Security**: Cognito, IAM, KMS, Certificate Manager
- **Monitoring**: CloudWatch, X-Ray, EventBridge
- **Backup**: AWS Backup, Cross-Region Replication

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