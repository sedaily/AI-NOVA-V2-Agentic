import boto3

apigateway = boto3.client('apigateway', region_name='us-east-1')
api_id = 'ieec2gpr0c'

print("CORS fixing...\n")

resources = apigateway.get_resources(restApiId=api_id)
resource_id = None
for resource in resources['items']:
    if resource.get('pathPart') == 'invoke-agent':
        resource_id = resource['id']
        break

if not resource_id:
    print("ERROR: invoke-agent resource not found")
    exit(1)

print(f"Resource ID: {resource_id}")

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
    print("Already exists")

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
    print("Integration response added")
except:
    print("Already exists")

apigateway.create_deployment(
    restApiId=api_id,
    stageName='prod'
)

print("\nCORS fixed! Test again.")
