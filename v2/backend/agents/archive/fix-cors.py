import boto3

apigateway = boto3.client('apigateway', region_name='us-east-1')

api_id = 'ieec2gpr0c'

print("🔧 CORS 수정 중...\n")

# 리소스 ID 가져오기
resources = apigateway.get_resources(restApiId=api_id)
resource_id = None
for resource in resources['items']:
    if resource.get('pathPart') == 'invoke-agent':
        resource_id = resource['id']
        break

if not resource_id:
    print("❌ invoke-agent 리소스를 찾을 수 없습니다")
    exit(1)

print(f"✅ 리소스 ID: {resource_id}")

# POST 메서드에 응답 헤더 추가
try:
    apigateway.put_method_response(
        restApiId=api_id,
        resourceId=resource_id,
        httpMethod='POST',
        statusCode='200',
        responseParameters={
            'method.response.header.Access-Control-Allow-Origin': True
        }
    )
    print("✅ POST 메서드 응답 헤더 추가")
except:
    print("⚠️  이미 존재")

# Integration 응답에 CORS 헤더 추가
try:
    apigateway.put_integration_response(
        restApiId=api_id,
        resourceId=resource_id,
        httpMethod='POST',
        statusCode='200',
        responseParameters={
            'method.response.header.Access-Control-Allow-Origin': "'*'"
        }
    )
    print("✅ Integration 응답 헤더 추가")
except:
    print("⚠️  이미 존재")

# 재배포
apigateway.create_deployment(
    restApiId=api_id,
    stageName='prod'
)

print("\n🎉 CORS 수정 완료!")
print("다시 테스트하세요")
