import boto3
import zipfile
import io

lambda_client = boto3.client('lambda', region_name='us-east-1')
sts = boto3.client('sts')

account_id = sts.get_caller_identity()['Account']
role_arn = f"arn:aws:iam::{account_id}:role/BedrockAgentExecutionRole"
function_name = 'bedrock-agent-api'

print(f"Deploying {function_name}...\n")

zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
    zip_file.write('api-gateway/lambda_function.py', 'lambda_function.py')

zip_buffer.seek(0)
zip_content = zip_buffer.read()

try:
    response = lambda_client.update_function_code(
        FunctionName=function_name,
        ZipFile=zip_content
    )
    print(f"Lambda updated: {response['FunctionArn']}")
except Exception as e:
    print(f"Error: {e}")
