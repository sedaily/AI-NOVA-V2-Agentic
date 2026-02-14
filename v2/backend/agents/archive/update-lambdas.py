import boto3
import zipfile
import io
import os

lambda_client = boto3.client('lambda', region_name='us-east-1')

agents = [
    'language-detector',
    'category-detector',
    'length-detector',
    'content-type-detector'
]

print("🔄 Lambda 함수 업데이트 중...\n")

for agent_name in agents:
    function_name = f"bedrock-{agent_name}"
    
    print(f"📦 {function_name} 업데이트 중...")
    
    # ZIP 파일 생성
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        lambda_file = os.path.join(agent_name, 'lambda_function.py')
        zip_file.write(lambda_file, 'lambda_function.py')
    
    zip_buffer.seek(0)
    zip_content = zip_buffer.read()
    
    try:
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        print(f"✅ {function_name} 업데이트 완료\n")
    except Exception as e:
        print(f"❌ {function_name} 업데이트 실패: {e}\n")

print("🎉 모든 Lambda 함수 업데이트 완료!")
print("\nAWS Console에서 다시 테스트하세요:")
print("https://us-east-1.console.aws.amazon.com/bedrock/home?region=us-east-1#/agents/JGEFIJJERA")
