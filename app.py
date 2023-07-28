#!/usr/bin/env python3
import aws_cdk as cdk
import yaml

from stacks.pipeline_stack import PipelineStack

with open('configs/config.yaml', 'r') as yml:
    config = yaml.safe_load(yml)

app = cdk.App()

pipeline_stack = PipelineStack(
    app,
    "PipelineStack",
    config=config,
    env=cdk.Environment(account=config['account']['account_id'], region=config['account']['region']),
    )

app.synth()
