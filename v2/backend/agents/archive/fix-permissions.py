import boto3
import json

iam = boto3.client('iam', region_name='us-east-1')
sts = boto3.client('sts')

print("🔧 IAM PassRole 권한 추가 중...")

# 현재 사용자 정보
identity = sts.get_caller_identity()
user_arn = identity['Arn']
account_id = identity['Account']

print(f"📋 현재 사용자: {user_arn}")
print(f"📋 Account ID: {account_id}")

# PassRole 정책 생성
policy_document = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "iam:PassRole",
            "Resource": f"arn:aws:iam::{account_id}:role/BedrockAgentExecutionRole"
        },
        {
            "Effect": "Allow",
            "Action": [
                "lambda:CreateFunction",
                "lambda:UpdateFunctionCode",
                "lambda:GetFunction",
                "lambda:ListFunctions"
            ],
            "Resource": "*"
        }
    ]
}

# 정책 이름
policy_name = "BedrockAgentDeployPolicy"

try:
    # 정책 생성
    response = iam.create_policy(
        PolicyName=policy_name,
        PolicyDocument=json.dumps(policy_document),
        Description="Policy for deploying Bedrock Agents"
    )
    policy_arn = response['Policy']['Arn']
    print(f"✅ 정책 생성 완료: {policy_arn}")
    
except iam.exceptions.EntityAlreadyExistsException:
    # 이미 존재하면 ARN 가져오기
    policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"
    print(f"⚠️  정책이 이미 존재합니다: {policy_arn}")

# 사용자에게 정책 연결
user_name = "yugyeong"

try:
    iam.attach_user_policy(
        UserName=user_name,
        PolicyArn=policy_arn
    )
    print(f"✅ {user_name} 사용자에게 정책 연결 완료")
    
except Exception as e:
    print(f"❌ 정책 연결 실패: {str(e)}")
    print("\n⚠️  관리자 권한이 필요합니다. AWS Console에서 수동으로 추가하세요:")
    print(f"   1. IAM → Users → {user_name}")
    print(f"   2. Add permissions → Attach policies")
    print(f"   3. {policy_name} 선택")

print("\n🎉 권한 설정 완료!")
print("\n다음 단계: python deploy-lambda.py 재실행")
