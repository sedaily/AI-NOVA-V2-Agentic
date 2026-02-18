import boto3

apigateway = boto3.client('apigateway', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')
sts = boto3.client('sts')

api_id = 'ieec2gpr0c'
account_id = sts.get_caller_identity()['Account']
region = 'us-east-1'

print("Recreating API Gateway integration...\n")

# 리소스 ID 가져오기
resources = apigateway.get_resources(restApiId=api_id)
resource_id = None
for resource in resources['items']:
    if resource.get('pathPart') == 'invoke-agent':
        resource_id = resource['id']
        break

if not resource_id:
    print("Error: Resource not found")
    exit(1)

print(f"Resource ID: {resource_id}")

# 기존 통합 삭제
try:
    apigateway.delete_integration(
        restApiId=api_id,
        resourceId=resource_id,
        httpMethod='POST'
    )
    print("Deleted old integration")
except:
    print("No old integration to delete")

# 새 통합 생성
lambda_arn = f'arn:aws:lambda:{region}:{account_id}:function:bedrock-agent-api'

apigateway.put_integration(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='POST',
    type='AWS_PROXY',
    integrationHttpMethod='POST',
    uri=f'arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
)
print("Created new integration")

# Lambda 권한 재설정
try:
    lambda_client.remove_permission(
        FunctionName='bedrock-agent-api',
        StatementId='apigateway-invoke'
    )
except:
    pass

lambda_client.add_permission(
    FunctionName='bedrock-agent-api',
    StatementId='apigateway-invoke',
    Action='lambda:InvokeFunction',
    Principal='apigateway.amazonaws.com',
    SourceArn=f'arn:aws:execute-api:{region}:{account_id}:{api_id}/*/*'
)
print("Lambda permission added")

# 재배포
apigateway.create_deployment(
    restApiId=api_id,
    stageName='prod'
)
print("\nDeployed!")
print(f"\nTest: https://{api_id}.execute-api.{region}.amazonaws.com/prod/invoke-agent")
