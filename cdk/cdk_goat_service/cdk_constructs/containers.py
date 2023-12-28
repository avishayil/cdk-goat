"""Containers CDK construct module."""
import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_ecr_assets as ecr_assets
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_elasticloadbalancingv2 as lb
from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as logs
from aws_cdk import aws_rds as rds
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_secretsmanager as sm
from cdk_ecr_deployment import DockerImageName, ECRDeployment
from constructs import Construct


class ContainersConstruct(Construct):
    """Containers CDK construct class."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc: ec2.IVpc,
        container_security_group: ec2.ISecurityGroup,
        load_balancer_security_group: ec2.ISecurityGroup,
        db: rds.DatabaseInstance,
        storage_bucket: s3.IBucket,
        *,
        prefix=None,
    ):
        """Construct initialization."""
        super().__init__(scope, id)

        db_secret = sm.Secret.from_secret_name_v2(
            self,
            "DBSecret",
            db.secret.secret_name,
        )

        ecr_repository = ecr.Repository(
            self,
            "ECRRepository",
            encryption=ecr.RepositoryEncryption.AES_256,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        ecr_image = ecr_assets.DockerImageAsset(
            self, "DVPWADockerImage", directory="cdk/containers/dvpwa"
        )

        ecr_deployment = ECRDeployment(  # noqa: F841
            self,
            "ECRDeployment",
            src=DockerImageName(name=ecr_image.image_uri),
            dest=DockerImageName(name=ecr_repository.repository_uri),
        )

        ecs_cluster = ecs.Cluster(self, "Cluster", vpc=vpc)

        cdk.Tags.of(ecs_cluster).add("App", "CDKGoat")

        ecs_task_role = iam.Role(
            self,
            "TaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            inline_policies={
                "GenericECSTask": iam.PolicyDocument(
                    assign_sids=True,
                    minimize=True,
                    statements=[
                        iam.PolicyStatement(
                            resources=["*"],
                            actions=[
                                "logs:CreateLogStream",
                                "logs:DescribeLogGroups",
                                "logs:DescribeLogStreams",
                                "logs:CreateLogGroup",
                                "logs:PutLogEvents",
                                "logs:PutRetentionPolicy",
                            ],
                        ),
                        iam.PolicyStatement(
                            resources=["*"], actions=["ec2:DescribeRegions"]
                        ),
                        iam.PolicyStatement(
                            resources=["*"],
                            actions=[
                                "cloudwatch:PutMetricData",
                                "cloudwatch:ListMetrics",
                            ],
                        ),
                        iam.PolicyStatement(
                            resources=["*"], actions=["rds-db:connect"]
                        ),
                    ],
                )
            },
        )

        db_secret.grant_read(ecs_task_role)
        storage_bucket.grant_read_write(ecs_task_role)

        ecs_task_execution_role = iam.Role(
            self,
            "TaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_managed_policy_arn(
                    self,
                    "ServiceRole",
                    managed_policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
                )
            ],
        )

        ecs_task_definition = ecs.FargateTaskDefinition(
            self,
            "TaskDefinition",
            cpu=256,
            memory_limit_mib=1024,
            execution_role=ecs_task_execution_role,
            task_role=ecs_task_role,
            runtime_platform=ecs.RuntimePlatform(
                operating_system_family=ecs.OperatingSystemFamily.LINUX,
                cpu_architecture=ecs.CpuArchitecture.X86_64,
            ),
        )

        ecs_backend_app_container = ecs_task_definition.add_container(  # noqa: F841
            "backend_app",
            container_name="backend_app",
            image=ecs.ContainerImage.from_ecr_repository(
                repository=ecr_repository, tag="latest"
            ),
            privileged=False,
            logging=ecs.LogDriver.aws_logs(
                stream_prefix="ContainerLogs-",
                log_retention=logs.RetentionDays.ONE_WEEK,
            ),
            port_mappings=[ecs.PortMapping(container_port=8000, host_port=8000)],
            secrets={
                "DB_NAME": ecs.Secret.from_secrets_manager(
                    db_secret,
                    "dbname",
                ),
                "DB_USER": ecs.Secret.from_secrets_manager(
                    db_secret,
                    "username",
                ),
                "DB_PASSWORD": ecs.Secret.from_secrets_manager(
                    db_secret,
                    "password",
                ),
                "DB_HOST": ecs.Secret.from_secrets_manager(
                    db_secret,
                    "host",
                ),
                "DB_PORT": ecs.Secret.from_secrets_manager(
                    db_secret,
                    "port",
                ),
            },
        )

        ecs_service = ecs_patterns.ApplicationLoadBalancedFargateService(  # noqa: F841
            self,
            "EcsService",
            cluster=ecs_cluster,
            task_definition=ecs_task_definition,
            security_groups=[container_security_group],
            task_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            public_load_balancer=True,
            enable_execute_command=True,
            assign_public_ip=True,
            desired_count=1,
            max_healthy_percent=200,
            min_healthy_percent=50,
            protocol=lb.ApplicationProtocol.HTTP,
            listener_port=80,
            enable_ecs_managed_tags=True,
        )

        ecs_service.load_balancer.set_attribute(
            key="routing.http.drop_invalid_header_fields.enabled", value="true"
        )

        ecs_service.target_group.configure_health_check(
            enabled=True,
            healthy_http_codes="200,301,302",
            port="8000",
            path="/",
            interval=cdk.Duration.seconds(amount=60),
            healthy_threshold_count=5,
            unhealthy_threshold_count=3,
            timeout=cdk.Duration.seconds(amount=30),
        )

        ecs_service.load_balancer.add_security_group(load_balancer_security_group)

        cdk.CfnOutput(self, "ClusterARN", value=ecs_cluster.cluster_arn)
        cdk.CfnOutput(
            self,
            "ApplicationLBDNS",
            value=ecs_service.load_balancer.load_balancer_dns_name,
        )

        self.ecs_task_role = ecs_task_role
        self.ecs_service_load_balancer = ecs_service.load_balancer
