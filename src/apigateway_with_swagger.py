from troposphere import Parameter, Ref, Template, apigateway

template = Template()

template.add_description("Example API Gateway from Swagger")

param_source_bucket = template.add_parameter(Parameter(
    "SourceBucket",
    Type="String",
    Description="Name of the bucket where Swagger file is stored"
))

param_ile_name = template.add_parameter(Parameter(
    "FileName",
    Type="String",
    Description="Name of the Swagger file inside S3 bucket"
))

api = template.add_resource(apigateway.RestApi(
    "API",
    Description="My API",
    Name="MyAPI",
    BodyS3Location=apigateway.S3Location(
        Bucket=Ref(param_source_bucket),
        Key=Ref(param_ile_name)
    )
))

api_deployment = template.add_resource(apigateway.Deployment(
    "APIDeployment",
    RestApiId=Ref(api),
    DependsOn=api.title,
))

api_stage = template.add_resource(apigateway.Stage(
    "APIStage",
    CacheClusterEnabled=False,
    DeploymentId=Ref(api_deployment),
    RestApiId=Ref(api),
    StageName="live",
))

print template.to_json()
