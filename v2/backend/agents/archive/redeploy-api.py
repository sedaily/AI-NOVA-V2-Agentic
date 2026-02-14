import boto3

apigateway = boto3.client('apigateway', region_name='us-east-1')
api_id = 'ieec2gpr0c'

print("Deploying API Gateway...\n")

try:
    response = apigateway.create_deployment(
        restApiId=api_id,
        stageName='prod',
        description='Redeploy for Lambda update'
    )
    print(f"Deployment created: {response['id']}")
    print(f"\nAPI URL: https://{api_id}.execute-api.us-east-1.amazonaws.com/prod/invoke-agent")
    print("\nTest again!")
except Exception as e:
    print(f"Error: {e}")
