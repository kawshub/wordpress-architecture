import aws_cdk as cdk
from aws_cdk import Duration, Stack
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_route53 as route53
from aws_cdk import aws_route53_targets as targets
from aws_cdk import aws_secretsmanager as secretsmanager
from aws_cdk import aws_ssm as ssm
from constructs import Construct


class ServiceStack(Stack):

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
        # シークレット読み込み
        ########################################################
        DBMasterUser = secretsmanager.Secret.from_secret_name_v2(
            self,
            "DBMasterUser",
            secret_name="DBMasterUser"
        )
        
        DBAccess = secretsmanager.Secret.from_secret_name_v2(
            self,
            "DBAccess",
            secret_name="DBAccess"
        )
        
        ########################################################
        # IAMの定義
        ########################################################
        task_role = iam.Role(
            self,
            "ECSTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )
        
        task_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonRDSFullAccess")
        )
        
        ########################################################
        #Route53の定義
        ########################################################
        hosted_zone = route53.HostedZone.from_lookup(
            self,
            "HostedZone",
            domain_name=config['dns']['domain_name']
        )

        ########################################################
        #Certificate Managerの定義
        ########################################################
        certificate = acm.Certificate(
            self,
            "Certificate",
            domain_name=config['dns']['domain_name'],
            validation=acm.CertificateValidation.from_dns()
        )

        ########################################################
        # ECSの定義
        ########################################################
        cluster = ecs.Cluster(
            self,
            "EcsCluster",
            vpc=vpc
        )

        task_definition = ecs.FargateTaskDefinition(
            self,
            "TaskDefinition",
            task_role=task_role,
            )
        
        container = task_definition.add_container(
            "EcsContainer",
            image=ecs.ContainerImage.from_ecr_repository(
                ecr.Repository.from_repository_arn(
                    self,
                    config['ecs']['container_name'],
                    repository_arn=config['ecs']['repository_arn']
                )
            ),
            secrets={
                "WORDPRESS_DB_HOST": ecs.Secret.from_secrets_manager(
                    secret=DBMasterUser, field="host"
                ),
                "WORDPRESS_DB_USER": ecs.Secret.from_secrets_manager(
                    secret=DBAccess, field="username"
                ),
                "WORDPRESS_DB_NAME": ecs.Secret.from_secrets_manager(
                    secret=DBAccess, field="dbname"
                ),
                "WORDPRESS_DB_PASSWORD": ecs.Secret.from_secrets_manager(
                    secret=DBAccess, field="password"
                ),
            },
            memory_limit_mib=512,
            logging=ecs.LogDrivers.aws_logs(stream_prefix="EcsContainer")
        )

        container.add_port_mappings(ecs.PortMapping(container_port=80))

        service = ecs.FargateService(
            self,
            "EcsService",
            cluster=cluster,
            task_definition=task_definition,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
        )

        ########################################################
        # LoadBalancerの定義
        ########################################################

        load_balancer = elbv2.ApplicationLoadBalancer(
            self,
            "LoadBalancer",
            vpc=vpc,
            internet_facing=True,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)
        )
        
        target_group = elbv2.ApplicationTargetGroup(
            self,
            "TargetGroup",
            port=80,
            vpc=vpc,
            protocol=elbv2.ApplicationProtocol.HTTP,
            health_check=elbv2.HealthCheck(
                path="/",
                port="80",
            ),
            target_type=elbv2.TargetType.IP
        )
        
        service.attach_to_application_target_group(target_group)
        
        listener = load_balancer.add_listener(
            "Listener",
            port=443,
            certificates=[certificate]
        )
        
        listener.add_target_groups(
            "AddTargetGroups",
            target_groups=[target_group]
        )
        
        service.connections.allow_from(load_balancer, port_range=ec2.Port.tcp(80))
        
        route53.ARecord(
            self,
            "Record",
            zone=hosted_zone,
            target=route53.RecordTarget.from_alias(
                targets.LoadBalancerTarget(load_balancer)
            ),
            record_name=config['dns']['domain_name'],
        )

        ########################################################
        #AutoScaling定義
        ########################################################
        autoscaling = service.auto_scale_task_count(
            max_capacity=config['autoscaling']['max_capacity'],
            min_capacity=config['autoscaling']['min_capacity'],
        )

        autoscaling.scale_on_cpu_utilization(
            "Scaling-Policy",
            target_utilization_percent=70,
            scale_in_cooldown=Duration.seconds(300),
            scale_out_cooldown=Duration.seconds(300)
        )
