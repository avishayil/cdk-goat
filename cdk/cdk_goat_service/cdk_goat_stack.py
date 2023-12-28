"""CDK Stack module."""

from aws_cdk import Stack
from constructs import Construct

from cdk_goat_service.cdk_constructs.containers import ContainersConstruct
from cdk_goat_service.cdk_constructs.db import DBConstruct
from cdk_goat_service.cdk_constructs.network import NetworkConstruct
from cdk_goat_service.cdk_constructs.storage import StorageConstruct


class CDKGoatStack(Stack):
    """CDK Stack class."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        """Stack initialization."""
        super().__init__(scope, construct_id, **kwargs)

        storage_construct = StorageConstruct(self, "StorageConstruct")

        network_construct = NetworkConstruct(self, "NetworkConstruct")

        db_construct = DBConstruct(
            self,
            "DBConstruct",
            vpc=network_construct.vpc,
            security_group=network_construct.db_sg,
        )

        containers_construct = ContainersConstruct(  # noqa: F841
            self,
            "ContainersConstruct",
            vpc=network_construct.vpc,
            container_security_group=network_construct.container_sg,
            load_balancer_security_group=network_construct.lb_sg,
            db=db_construct.db_cluster,
            storage_bucket=storage_construct.storage_bucket,
        )

        # Declare dependencies

        containers_construct.node.add_dependency(db_construct)
