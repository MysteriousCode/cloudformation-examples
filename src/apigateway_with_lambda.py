from troposphere import GetAtt, Ref, Template, Parameter, Join
from troposphere import iam
from troposphere import awslambda
from troposphere import apigateway
from awacs import aws, sts

template = Template()

template.add_description("Image gateway")

param_lambda_source_bucket = template.add_parameter(Parameter(
    "LambdaSourceBucket",
    Type="String",
    Description="Name of the bucket where lambda function sources is stored"
))

param_lambda_file_name = template.add_parameter(Parameter(
    "LambdaFileName",
    Type="String",
    Description="Name of the ZIP file with lambda function sources inside S3 bucket"
))

lambda_role = template.add_resource(iam.Role(
    "LambaRole",
    AssumeRolePolicyDocument=aws.Policy(
        Statement=[
            aws.Statement(
                Effect=aws.Allow,
                Action=[sts.AssumeRole],
                Principal=aws.Principal(
                    "Service", ["lambda.amazonaws.com"]
                )
            )
        ]
    ),
    Policies=[
        iam.Policy(
            PolicyName="LambdaPolicy",
            PolicyDocument=aws.Policy(
                Statement=[
                    aws.Statement(
                        Effect=aws.Allow,
                        Action=[
                            aws.Action("logs", "CreateLogGroup"),
                            aws.Action("logs", "CreateLogStream"),
                            aws.Action("logs", "PutLogEvents"),
                        ],
                        Resource=["arn:aws:logs:*:*:*"]
                    )
                ]
            )
        )
    ]
))

lambda_function = template.add_resource(awslambda.Function(
    "Lambda",
    Code=awslambda.Code(
        S3Bucket=Ref(param_lambda_source_bucket),
        S3Key=Ref(param_lambda_file_name)
    ),
    Handler="lambda.lambda_handler",
    MemorySize=128,
    Role=GetAtt(lambda_role, "Arn"),
    Runtime="python2.7",
    Timeout=30
))

api = template.add_resource(apigateway.RestApi(
    "API",
    Description="My API",
    Name="MyAPI"
))

api_lambda_permission = template.add_resource(awslambda.Permission(
    "APILambdaPermission",
    Action="lambda:InvokeFunction",
    FunctionName=Ref(lambda_function),
    Principal="apigateway.amazonaws.com",
    SourceArn=Join("", [
        "arn:aws:execute-api:",
        Ref("AWS::Region"),
        ":",
        Ref("AWS::AccountId"),
        ":",
        Ref(api),
        "/*/GET/*"
    ])
))

api_first_resource = template.add_resource(apigateway.Resource(
    "APIFirstResource",
    ParentId=GetAtt(api, "RootResourceId"),
    PathPart="{param1}",
    RestApiId=Ref(api)
))

api_first_method = template.add_resource(apigateway.Method(
    "APIFirstResourceMethodGET",
    ApiKeyRequired=False,
    AuthorizationType="NONE",
    HttpMethod="GET",
    ResourceId=Ref(api_first_resource),
    RestApiId=Ref(api),
    Integration=apigateway.Integration(
        Type="AWS",
        IntegrationHttpMethod="POST",
        Uri=Join("", [
            "arn:aws:apigateway:",
            Ref("AWS::Region"),
            ":lambda:path/2015-03-31/functions/",
            GetAtt(lambda_function, "Arn"),
            "/invocations"
        ]),
        RequestTemplates={
            "application/json": Join("", [
                "{\"param1\": \"$input.params('param1')\", \"param2\": \"$input.params('param2')\"}"
            ])
        },
        IntegrationResponses=[
            apigateway.IntegrationResponse(
                "IntegrationResponse",
                StatusCode="200",
                ResponseTemplates={
                    "application/json": "$input.params('whatever')"
                }
            ),
            apigateway.IntegrationResponse(
                "IntegrationResponse",
                StatusCode="404",
                SelectionPattern="[a-zA-Z]+.*",  # any error
                ResponseTemplates={
                    "application/json": "$input.params('whatever')"
                }
            ),
        ]
    ),
    RequestParameters={
        "method.request.path.param1": True,
        "method.request.querystring.param2": True
    },
    MethodResponses=[
        apigateway.MethodResponse(
            "APIResponse",
            StatusCode="200"
        ),
        apigateway.MethodResponse(
            "APIResponse",
            StatusCode="404"
        )
    ]
))

api_deployment = template.add_resource(apigateway.Deployment(
    "APIDeployment",
    RestApiId=Ref(api),
    StageName="live",
    StageDescription=apigateway.StageDescription(
        CacheClusterEnabled=False,
    )
))

print template.to_json()
