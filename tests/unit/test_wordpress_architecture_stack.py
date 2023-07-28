import aws_cdk as core
import aws_cdk.assertions as assertions

from wordpress_architecture.wordpress_architecture_stack import WordpressArchitectureStack

# example tests. To run these tests, uncomment this file along with the example
# resource in wordpress_architecture/wordpress_architecture_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = WordpressArchitectureStack(app, "wordpress-architecture")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
