# Bedrock Agents 배포 가이드

## 구조
```
backend/agents/
├── language-detector/
│   ├── lambda_function.py
│   └── agent-config.json
├── category-detector/
│   ├── lambda_function.py
│   └── agent-config.json
├── length-detector/
│   ├── lambda_function.py
│   └── agent-config.json
├── supervisor/
│   └── agent-config.json
└── deploy-agents.sh
```

## 배포 순서

### 1. IAM Role 생성
```bash
# Lambda 실행 역할
aws iam create-role \
  --role-name lambda-execution-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Bedrock Agent 실행 역할
aws iam create-role \
  --role-name AmazonBedrockExecutionRoleForAgents \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "bedrock.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'
```

### 2. Lambda 함수 배포
```bash
cd backend/agents

# Language Detector
cd language-detector
zip -r function.zip lambda_function.py
aws lambda create-function \
  --function-name language-detector \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip
cd ..

# Category Detector
cd category-detector
zip -r function.zip lambda_function.py
aws lambda create-function \
  --function-name category-detector \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip
cd ..

# Length Detector
cd length-detector
zip -r function.zip lambda_function.py
aws lambda create-function \
  --function-name length-detector \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip
cd ..
```

### 3. Bedrock Agent 생성 (AWS Console)

#### Language Detection Agent
1. AWS Console → Bedrock → Agents → Create Agent
2. Agent name: `language-detection-agent`
3. Model: `Claude 3 Sonnet`
4. Instructions: `당신은 텍스트의 언어를 감지하는 전문가입니다.`
5. Action Group 추가:
   - Name: `language-detection`
   - Lambda: `language-detector`
   - API Schema: `language-detector/agent-config.json` 참고

#### Category Detection Agent
1. Agent name: `category-detection-agent`
2. Model: `Claude 3 Sonnet`
3. Instructions: `당신은 기사의 카테고리를 분류하는 전문가입니다.`
4. Action Group: `category-detector` Lambda

#### Length Detection Agent
1. Agent name: `length-detection-agent`
2. Model: `Claude 3 Sonnet`
3. Instructions: `당신은 텍스트의 길이를 분석하는 전문가입니다.`
4. Action Group: `length-detector` Lambda

### 4. Supervisor Agent 생성
1. Agent name: `supervisor-agent`
2. Model: `Claude 3 Sonnet`
3. Instructions: `supervisor/agent-config.json` 참고
4. Agent Collaboration 설정:
   - Type: `SUPERVISOR_ROUTER`
   - Collaborators: 위 3개 에이전트 추가

### 5. 테스트
```bash
# Bedrock Agent 호출
aws bedrock-agent-runtime invoke-agent \
  --agent-id SUPERVISOR_AGENT_ID \
  --agent-alias-id ALIAS_ID \
  --session-id test-session \
  --input-text "삼성전자 주가가 오늘 5% 상승했다"
```

## 비용
- Lambda: 무료 티어 (월 100만 요청)
- Bedrock Agent: 사용량 기반
- Claude 3 Sonnet: 입력 $3/MTok, 출력 $15/MTok

## 다음 단계
1. Supervisor Agent 테스트
2. 기존 서비스(b1, p1, r1 등)와 통합
3. 프론트엔드 연결
