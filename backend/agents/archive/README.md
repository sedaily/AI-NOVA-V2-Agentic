# Archive

이 폴더에는 개발 과정에서 사용했던 스크립트들이 보관되어 있습니다.

## 보관된 파일들

### Agent 생성 스크립트
- `create-agent.py` - Bedrock Agent 생성
- `create-alias.py` - Agent Alias 생성
- `update-agent-model.py` - Agent 모델 업데이트

### API Gateway 설정
- `create-api-gateway.py` - API Gateway 생성
- `recreate-integration.py` - Integration 재생성
- `redeploy-api.py` - API 재배포

### Lambda 배포
- `deploy-lambda.py` - Lambda 배포
- `deploy-lambda.sh` - Lambda 배포 스크립트
- `deploy-api-lambda.py` - API Lambda 배포
- `deploy-api-simple.py` - 간단한 API 배포
- `update-lambdas.py` - Lambda 업데이트

### CORS 수정
- `fix-cors.py` - CORS 수정 (복잡한 버전)
- `fix-cors-simple.py` - CORS 수정 (간단한 버전)
- **현재 사용 중**: `../fix-cors-now.py`

### 기타
- `fix-permissions.py` - 권한 수정
- `list-aliases.py` - Alias 목록 조회
- `recreate-alias.py` - Alias 재생성
- `setup-iam-role.sh` - IAM Role 설정
- `deploy-agents.sh` - Agent 배포
- `deploy-step-functions.py` - Step Functions 배포
- `step-functions-definition.json` - Step Functions 정의
- `add-service-caller.py` - Service Caller 추가

## 현재 사용 중인 파일

프로젝트 루트에 남아있는 파일들:
- `fix-cors-now.py` - CORS 수정 (운영 중)
- `api-gateway/lambda_function.py` - API Gateway Lambda (운영 중)
- `BEDROCK-PIPELINE.md` - 구현 문서
- `README.md` - 프로젝트 설명

## 참고

이 파일들은 향후 참고용으로 보관되며, 필요시 다시 사용할 수 있습니다.
