# 배포 가이드 (Deployment Guide)

## 🚀 빠른 시작

### 전체 자동 배포
```bash
cd scripts
./deploy-all-new.sh [서비스명] [리전] [환경]

# 예시
./deploy-all-new.sh tem1 us-east-1 prod
./deploy-all-new.sh news us-east-1 dev
```

### 2단계 배포 (권장)
중간에 확인이 필요하거나 문제가 발생할 경우:

```bash
# Phase 1: 인프라 구축
cd scripts
./deploy-phase1-infra.sh tem1 us-east-1

# Phase 2: 코드 배포
./deploy-phase2-code.sh tem1 us-east-1
```

## 📋 사전 준비사항

### 1. 환경변수 설정
```bash
# backend/.env 파일 생성 (backend/.env.template 참고)
cp backend/.env.template backend/.env
# 편집기로 열어서 값 수정

# frontend/.env 파일 생성 (frontend/.env.template 참고)
cp frontend/.env.template frontend/.env
# 편집기로 열어서 값 수정
```

### 2. AWS 설정
```bash
# AWS CLI 설정 확인
aws configure list

# 권한 확인
aws sts get-caller-identity
```

## 🏗️ 배포 단계 설명

### Phase 1: 인프라 구축 (1-8단계)
1. **DynamoDB 테이블 생성** - 데이터 저장소
2. **Lambda 함수 생성** - 백엔드 로직
3. **REST API Gateway** - HTTP API
4. **WebSocket API** - 실시간 통신
5. **Lambda 권한 설정** - IAM 정책
6. **Lambda 코드 초기 배포** - 기본 코드
7. **S3 버킷 생성** - 정적 파일 호스팅
8. **CloudFront 설정** - CDN 배포

### Phase 2: 코드 배포 및 설정 (9-13단계)
9. **프론트엔드 빌드 및 배포** - React 앱
10. **설정 파일 업데이트** - 환경별 설정
11. **백엔드 설정 업데이트** - API 설정
12. **프론트엔드 설정 업데이트** - UI 설정
13. **Lambda 환경변수 업데이트** - 최종 설정

## 🛠️ 문제 해결

### 중간에 멈춘 경우
```bash
# 상태 확인
cat ../.deployment-status

# 특정 단계부터 재시작
cd scripts
./deploy-phase2-code.sh
```

### Phase 사이 일시정지 활성화
```bash
PAUSE_BETWEEN_PHASES=true ./deploy-all-new.sh tem1
```

### 개별 스크립트 실행
```bash
cd scripts
./01-create-dynamodb.sh    # DynamoDB만
./06-deploy-lambda-code.sh  # Lambda 코드만
./09-deploy-frontend.sh     # 프론트엔드만
```

## 📊 배포 확인

### 상태 파일
- `.deployment-status` - 배포 진행 상태
- `.api-ids` - 생성된 API ID
- `.cloudfront-url` - CloudFront URL
- `endpoints.txt` - 모든 엔드포인트

### 로그 확인
```bash
# Lambda 로그
aws logs tail /aws/lambda/tem1-prompt-crud --follow

# DynamoDB 테이블 확인
aws dynamodb list-tables --region us-east-1
```

## 🔄 재배포

### 프론트엔드만 업데이트
```bash
cd frontend
npm run build
aws s3 sync build/ s3://tem1-frontend --delete
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths '/*'
```

### Lambda 코드만 업데이트
```bash
cd scripts
./06-deploy-lambda-code.sh
```

## 🗑️ 리소스 정리

```bash
# 주의: 모든 리소스가 삭제됩니다!
cd scripts
./cleanup-all.sh tem1 us-east-1
```

## 💡 팁

1. **서비스명 규칙**: 소문자, 하이픈 사용 (예: news-service)
2. **리전 선택**: us-east-1 권장 (CloudFront 호환)
3. **환경 구분**: prod, dev, staging
4. **테스트**: 먼저 dev 환경에서 테스트 후 prod 배포

## 📚 관련 문서

- [TEM1_TROUBLESHOOTING_GUIDE.md](TEM1_TROUBLESHOOTING_GUIDE.md) - 문제 해결
- [backend/.env.template](backend/.env.template) - 백엔드 환경변수
- [frontend/.env.template](frontend/.env.template) - 프론트엔드 환경변수
- [terraform/](terraform/) - 테라폼 설정 (선택사항)