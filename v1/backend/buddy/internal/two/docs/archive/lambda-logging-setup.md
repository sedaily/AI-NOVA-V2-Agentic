# Lambda 함수 CloudWatch Logs 설정 가이드

## 문제
- WebSocket 관련 로그는 있으나 REST API (prompt, conversation, usage) 로그 그룹이 없음

## 확인 필요 사항

### 1. Lambda 함수 이름 확인
AWS Console에서 다음 Lambda 함수들이 존재하는지 확인:
- `p2-two-prompt-handler` 또는 유사한 이름
- `p2-two-conversation-handler`
- `p2-two-usage-handler`

### 2. Lambda 함수 IAM Role 권한 확인

각 Lambda 함수의 실행 역할(Execution Role)에 다음 권한이 있어야 함:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:us-east-1:*:*"
    }
  ]
}
```

### 3. 로그 그룹 수동 생성 (필요시)

CloudWatch Console에서 다음 로그 그룹 생성:
- `/aws/lambda/p2-two-prompt-handler`
- `/aws/lambda/p2-two-conversation-handler`
- `/aws/lambda/p2-two-usage-handler`

### 4. Lambda 함수 환경 변수 확인

각 Lambda 함수에 다음 환경 변수가 설정되어 있는지 확인:
- `LOG_LEVEL`: INFO
- `PROMPTS_TABLE`: p2-two-prompts-two
- `FILES_TABLE`: p2-two-files-two
- `CONVERSATIONS_TABLE`: p2-two-conversations
- `USAGE_TABLE`: p2-two-usage

### 5. API Gateway 로깅 설정

API Gateway 콘솔에서:
1. API 선택 (`pisnqqgu75`)
2. Settings → CloudWatch Settings
3. CloudWatch Logs 활성화
4. Log level: INFO
5. Log full requests/responses: Yes (디버깅용)

### 6. 테스트 방법

Lambda 함수 직접 테스트:
```bash
aws lambda invoke \
  --function-name p2-two-prompt-handler \
  --payload '{"httpMethod":"GET","path":"/prompts/11"}' \
  response.json
```

로그 확인:
```bash
aws logs tail /aws/lambda/p2-two-prompt-handler --follow
```

## 즉시 해결 방법

1. AWS Console → Lambda → Functions
2. REST API 함수 선택
3. Configuration → Monitoring and operations tools
4. CloudWatch Logs 섹션 확인
5. "View logs in CloudWatch" 클릭하여 로그 그룹 자동 생성

## 참고사항
- Lambda 함수가 처음 실행될 때 로그 그룹이 자동 생성됨
- 함수가 한 번도 실행되지 않았다면 로그 그룹이 없을 수 있음
- IAM 권한이 없으면 로그가 기록되지 않음