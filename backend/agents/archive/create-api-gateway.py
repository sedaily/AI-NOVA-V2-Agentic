import boto3
import json

apigateway = boto3.client('apigateway', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')
sts = boto3.client('sts')

account_id = sts.get_caller_identity()['Account']
region = 'us-east-1'
lambda_arn = f'arn:aws:lambda:{region}:{account_id}:function:bedrock-agent-api'

print("🚀 API Gateway 생성 중...\n")

# 1. REST API 생성
api_response = apigateway.create_rest_api(
    name='BedrockAgentAPI',
    description='API Gateway for Bedrock Agent',
    endpointConfiguration={'types': ['REGIONAL']}
)

api_id = api_response['id']
print(f"✅ REST API 생성 완료: {api_id}")

# 2. Root 리소스 가져오기
resources = apigateway.get_resources(restApiId=api_id)
root_id = resources['items'][0]['id']

# 3. /invoke-agent 리소스 생성
resource_response = apigateway.create_resource(
    restApiId=api_id,
    parentId=root_id,
    pathPart='invoke-agent'
)
resource_id = resource_response['id']
print(f"✅ 리소스 생성 완료: /invoke-agent")

# 4. POST 메서드 생성
apigateway.put_method(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='POST',
    authorizationType='NONE'
)

# 5. Lambda 통합
apigateway.put_integration(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='POST',
    type='AWS_PROXY',
    integrationHttpMethod='POST',
    uri=f'arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
)

# 6. CORS 설정
apigateway.put_method(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='OPTIONS',
    authorizationType='NONE'
)

apigateway.put_method_response(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='OPTIONS',
    statusCode='200',
    responseParameters={
        'method.response.header.Access-Control-Allow-Headers': True,
        'method.response.header.Access-Control-Allow-Methods': True,
        'method.response.header.Access-Control-Allow-Origin': True
    }
)

apigateway.put_integration(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='OPTIONS',
    type='MOCK',
    requestTemplates={'application/json': '{"statusCode": 200}'}
)

apigateway.put_integration_response(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='OPTIONS',
    statusCode='200',
    responseParameters={
        'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
        'method.response.header.Access-Control-Allow-Methods': "'POST,OPTIONS'",
        'method.response.header.Access-Control-Allow-Origin': "'*'"
    }
)

print("✅ CORS 설정 완료")

# 7. Lambda 권한 추가
try:
    lambda_client.add_permission(
        FunctionName='bedrock-agent-api',
        StatementId='apigateway-invoke',
        Action='lambda:InvokeFunction',
        Principal='apigateway.amazonaws.com',
        SourceArn=f'arn:aws:execute-api:{region}:{account_id}:{api_id}/*/*'
    )
    print("✅ Lambda 권한 추가 완료")
except:
    print("⚠️  Lambda 권한 이미 존재")

# 8. 배포
deployment = apigateway.create_deployment(
    restApiId=api_id,
    stageName='prod'
)
print("✅ API 배포 완료")

# 9. URL 출력
api_url = f"https://{api_id}.execute-api.{region}.amazonaws.com/prod/invoke-agent"
print(f"\n🎉 API Gateway 생성 완료!")
print(f"\n📋 API URL: {api_url}")
print(f"\n다음: 프론트엔드에서 이 URL 사용")
print(f"ChatInput.jsx에서 'YOUR_API_GATEWAY_URL'을 다음으로 교체:")
print(f"https://{api_id}.execute-api.{region}.amazonaws.com/prod")
