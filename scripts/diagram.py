from diagrams import Cluster, Diagram, Edge
from diagrams.aws.compute import ECS
from diagrams.aws.database import RDS
from diagrams.aws.network import ALB
from diagrams.aws.storage import S3
from diagrams.custom import Custom

with Diagram("CDK Goat Architecture", filename="../images/cdk_goat_architecture"):
    hacker = Custom(label="Malicous\nUser", icon_path="../images/hacker.png")
    user = Custom(label="Legitimate\nUser", icon_path="../images/legitimate_user.png")
    with Cluster("AWS Cloud"):
        s3 = S3("Uploads\nBucket")
        with Cluster("VPC"):
            with Cluster("Public Subnet"):
                with Cluster("ECS Cluster"):
                    web_container = ECS("DVPWA\nContainer")

                alb = ALB("Application\nLoad Balancer")
                rds_instance = RDS("DB\nInstance")

                user >> alb
                hacker >> Edge(style="dotted", color="red") >> alb
                hacker >> Edge(style="dotted", color="red") >> web_container
                hacker >> Edge(style="dotted", color="red") >> rds_instance
                hacker >> Edge(style="dotted", color="red") >> s3

                alb >> web_container
                web_container >> s3
                web_container >> rds_instance
