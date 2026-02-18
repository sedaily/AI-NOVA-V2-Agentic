import boto3
import json
import sys
import io

# Windows 콘솔 인코딩 문제 해결
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

apigateway = boto3.client('apigateway', region_name='us-east-1')
api_id = 'ieec2gpr0c'

print("CORS fixing...\n")

# Resource finding
resources = apigateway.get_resources(restApiId=api_id)
resource_id = None
for resource in resources['items']:
    if resource.get('pathPart') == 'invoke-agent':
        resource_id = resource['id']
        print(f"Resource ID: {resource_id}")
        break

if not resource_id:
    print("ERROR: invoke-agent resource not found")
    exit(1)

print(f"Resource ID: {resource_id}")

# OPTIONS method
try:
    apigateway.put_method(
        restApiId=api_id,
        resourceId=resource_id,
        httpMethod='OPTIONS',
        authorizationType='NONE'
    )
    print("OPTIONS method added")
except:
    print("OPTIONS method exists")

# OPTIONS method response
try:
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
    print("OPTIONS method response added")
except:
    print("OPTIONS method response exists")

# OPTIONS integration
try:
    apigateway.put_integration(
        restApiId=api_id,
        resourceId=resource_id,
        httpMethod='OPTIONS',
        type='MOCK',
        requestTemplates={
            'application/json': '{"statusCode": 200}'
        }
    )
    print("OPTIONS integration added")
except:
    print("OPTIONS integration exists")

# OPTIONS integration response
try:
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
    print("OPTIONS integration response added")
except:
    print("OPTIONS integration response exists")

# POST method response
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
    print("POST method response added")
except:
    print("POST method response exists")

# POST integration response
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
    print("POST integration response added")
except Exception as e:
    print(f"POST integration response error: {e}")

# Deploy
print("\nDeploying...")
apigateway.create_deployment(
    restApiId=api_id,
    stageName='prod',
    description='CORS fix deployment'
)

print("\nCORS fixed!")
print("Test URL: https://ieec2gpr0c.execute-api.us-east-1.amazonaws.com/prod/invoke-agent")
