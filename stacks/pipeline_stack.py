import aws_cdk as cdk
import yaml
from aws_cdk import Stack, Stage
from aws_cdk import pipelines as pipelines
from constructs import Construct

from stacks.database_stack import DatabaseStack
from stacks.network_stack import NetworkStack
from stacks.service_stack import ServiceStack

with open('configs/config.yaml', 'r') as yml:
    config = yaml.safe_load(yml)

class ApplicationStage(Stage):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        network_stack = NetworkStack(
            self,
            "NetworkStack",
            config=config
        )
        
        database_stack = DatabaseStack(
            self,
            "DatabaseStack",
            config=config
        )
        
        database_stack.add_dependency(network_stack)

        service_stack = ServiceStack(
            self,
            "ServiceStack",
            config=config
        )

        service_stack.add_dependency(database_stack)

class PipelineStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, config, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        pipeline = pipelines.CodePipeline(self, "Pipeline",
            synth=pipelines.ShellStep("Synth",
                input = pipelines.CodePipelineSource.connection(
                    config['pipeline']['repository_name'] ,
                    config['pipeline']['branch'] ,
                    connection_arn=config['pipeline']['connection_arn']
                ),
                commands=[
                    "npm install -g aws-cdk",
                    "pip install -r requirements.txt",
                    "cdk synth"
                ],
            )
        )
    
        pipeline.add_stage(ApplicationStage(self, "ApplicationStage",
            env=cdk.Environment(
                account=config['account']['account_id'],
                region=config['account']['region']
            )
        ))