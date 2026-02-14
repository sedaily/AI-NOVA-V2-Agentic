# Phase 1 실행 가이드

## 사전 준비

### 1. AWS CLI 설치 확인
```bash
aws --version
# AWS CLI 2.x 이상 필요
```

### 2. AWS 자격 증명 설정
```bash
aws configure
# AWS Access Key ID: YOUR_ACCESS_KEY
# AWS Secret Access Key: YOUR_SECRET_KEY
# Default region name: us-east-1
# Default output format: json
```

### 3. Bedrock 모델 접근 권한 확인
```bash
# AWS Console → Bedrock → Model access
# Claude 3.5 Sonnet 모델 활성화 필요
```

---

## 실행 순서

### Step 1: IAM Role 생성
```bash
cd backend/agents
bash setup-iam-role.sh
```

**예상 출력**:
```
🚀 Phase 1: IAM Role 생성 시작...
✅ Trust Policy 파일 생성 완료
📝 IAM Role 생성 중...
✅ IAM Role 생성 완료
📝 Lambda 실행 권한 추가 중...
✅ Lambda 실행 권한 추가 완료
📝 Bedrock 정책 생성 중...
✅ Bedrock 정책 추가 완료

🎉 Phase 1 완료!
📋 Role ARN: arn:aws:iam::123456789012:role/BedrockAgentExecutionRole
```

### Step 2: Lambda 함수 배포
```bash
bash deploy-lambda.sh
```

**예상 출력**:
```
🚀 Phase 1: Lambda 함수 배포 시작...
📋 Account ID: 123456789012
📋 Role ARN: arn:aws:iam::123456789012:role/BedrockAgentExecutionRole

📦 language-detector Lambda 배포 중...
✅ bedrock-language-detector 생성 완료
📋 ARN: arn:aws:lambda:us-east-1:123456789012:function:bedrock-language-detector

📦 category-detector Lambda 배포 중...
✅ bedrock-category-detector 생성 완료
📋 ARN: arn:aws:lambda:us-east-1:123456789012:function:bedrock-category-detector

📦 length-detector Lambda 배포 중...
✅ bedrock-length-detector 생성 완료
📋 ARN: arn:aws:lambda:us-east-1:123456789012:function:bedrock-length-detector

📦 content-type-detector Lambda 배포 중...
✅ bedrock-content-type-detector 생성 완료
📋 ARN: arn:aws:lambda:us-east-1:123456789012:function:bedrock-content-type-detector

🎉 Phase 1 완료!
```

### Step 3: 확인
```bash
# Lambda 함수 목록 확인
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `bedrock-`)].FunctionName'

# IAM Role 확인
aws iam get-role --role-name BedrockAgentExecutionRole
```

---

## 문제 해결

### 에러: "Role cannot be assumed by bedrock.amazonaws.com"
**해결**: IAM Role이 생성되는 데 시간이 걸립니다. 1-2분 대기 후 재시도

### 에러: "Access Denied"
**해결**: AWS 자격 증명에 IAM 및 Lambda 생성 권한이 있는지 확인

### 에러: "Model access denied"
**해결**: AWS Console → Bedrock → Model access에서 Claude 3.5 Sonnet 활성화

---

## 다음 단계

Phase 1 완료 후:
1. ✅ IAM Role 생성됨
2. ✅ Lambda 함수 4개 배포됨
3. ⏭️ **Phase 2**: Bedrock Agent 생성 (AWS Console)

**Phase 2로 이동**: `BEDROCK-PIPELINE.md` 참고
