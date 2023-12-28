"""Network CDK construct module."""
from aws_cdk import aws_ec2 as ec2
from constructs import Construct

from cdk.cdk_goat_service.cdk_constructs.constants import ALLOWED_CIDR, VPC_CIDR


class NetworkConstruct(Construct):
    """Network CDK construct class."""

    def __init__(self, scope: Construct, id: str, *, prefix=None):
        """Construct initialization."""
        super().__init__(scope, id)

        network_vpc = ec2.Vpc(
            self,
            "Vpc",
            max_azs=2,
            ip_addresses=ec2.IpAddresses.cidr(VPC_CIDR),
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Private",
                    cidr_mask=24,
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                ),
                ec2.SubnetConfiguration(
                    name="Public",
                    cidr_mask=24,
                    subnet_type=ec2.SubnetType.PUBLIC,
                    map_public_ip_on_launch=True,
                ),
            ],
        )

        db_sg = ec2.SecurityGroup(
            self,
            "DBSG",
            vpc=network_vpc,
            description="DB security group",
            allow_all_outbound=False,
        )

        container_sg = ec2.SecurityGroup(
            self,
            "ContainerSG",
            vpc=network_vpc,
            description="ECS Container security group",
            allow_all_outbound=True,
        )

        lb_sg = ec2.SecurityGroup(
            self,
            "LBSG",
            vpc=network_vpc,
            description="ECS Container security group",
            allow_all_outbound=False,
        )

        lb_sg.connections.allow_from(
            ec2.Peer.ipv4(cidr_ip=ALLOWED_CIDR),
            port_range=ec2.Port.tcp(80),
            description="Allow traffic from development endpoints",
        )

        db_sg.connections.allow_from(
            ec2.Peer.ipv4(cidr_ip=ALLOWED_CIDR),
            port_range=ec2.Port.tcp(5432),
            description="Allow traffic to database from application containers",
        )

        lb_sg.connections.allow_to(
            ec2.Peer.security_group_id(
                security_group_id=container_sg.security_group_id
            ),
            port_range=ec2.Port.tcp(8000),
            description="Allow traffic from load balancer to application containers",
        )

        self.vpc = network_vpc
        self.db_sg = db_sg
        self.container_sg = container_sg
        self.lb_sg = lb_sg
