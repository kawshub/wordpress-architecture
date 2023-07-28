from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_rds as rds
from aws_cdk import aws_secretsmanager as secretsmanager
from aws_cdk import aws_ssm as ssm
from constructs import Construct


class DatabaseStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, config, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        ########################################################
        # パラメータ読み込み
        ########################################################
        vpc = ec2.Vpc.from_lookup(
            self,
            "VPC",
            vpc_id=ssm.StringParameter.value_from_lookup(
                self,
                parameter_name="VpcID",
            ),
        )

        ########################################################
        # RDSの定義
        ########################################################
        rds_cluster = rds.DatabaseCluster(
            self,
            "Database",
            engine=rds.DatabaseClusterEngine.aurora_mysql(version=rds.AuroraMysqlEngineVersion.VER_2_11_1),
            instance_props=rds.InstanceProps(
                instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.SMALL),
                vpc_subnets=ec2.SubnetSelection(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ),
                vpc=vpc
            ),
            credentials=rds.Credentials.from_generated_secret(
                "rdsmaster",
                secret_name="DBMasterUser",
            ),
        )
        
        rds_cluster.connections.allow_default_port_from(ec2.Peer.ipv4(config['vpc']['cidr']))
        ########################################################
        # SystemsManagerにパラメータ出力
        ########################################################
        ssm_parameter = ssm.StringParameter(self, "SsmParameter",
            parameter_name="ClusterIdentifier",
            string_value=rds_cluster.cluster_identifier
        )

        ########################################################
        # SecretsManagerにパラメータ出力
        ########################################################
        secret = secretsmanager.Secret(
            self,
            "DBAccess",
            secret_name="DBAccess",
            generate_secret_string=secretsmanager.SecretStringGenerator(
            secret_string_template='{"username": "myusername", "dbname": "mydbname", "password": "mypassword"}',
                generate_string_key="password",
                exclude_punctuation=True,
            )
        )