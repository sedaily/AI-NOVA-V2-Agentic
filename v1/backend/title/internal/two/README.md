# t1.sedaily.ai - Nexus AI Title Generation Service

## 📋 개요
AI 기반 제목 생성 서비스 (t1.sedaily.ai)  
Claude Opus 4.5 API를 사용한 실시간 대화형 인터페이스

## 🏗️ 아키텍처
- **Frontend**: React SPA (S3 + CloudFront)
- **Backend**: Lambda Functions (Python 3.11)
- **AI Provider**: Anthropic Claude Opus 4.5
- **인증**: AWS Cognito
- **데이터베이스**: DynamoDB

## 📁 프로젝트 구조
```
.
├── frontend/           # React 애플리케이션
├── backend/           # Lambda 함수 코드
│   ├── handlers/      # WebSocket & REST 핸들러
│   └── lib/          # 공통 라이브러리
├── config/           # 환경 설정
│   └── t1-production.env  # 프로덕션 설정
├── logs/            # 배포 로그
└── old-*/           # 백업 파일들
```

## 🚀 배포 스크립트

### 메인 배포 스크립트
```bash
./deploy-main.sh
```
대화형 메뉴를 통해 배포 옵션 선택:
1. 전체 배포 (프론트엔드 + 백엔드)
2. 프론트엔드만 배포
3. 백엔드만 배포
4. Lambda 패키징만
5. Lambda 환경변수 업데이트
6. CloudFront 캐시 무효화

### 개별 배포 스크립트
```bash
./deploy-frontend.sh   # 프론트엔드만 배포
./deploy-backend.sh    # 백엔드만 배포  
./update-env.sh       # 환경변수만 업데이트
```

## 🔧 설정

### 환경 설정
`config/t1-production.env` 파일에서 모든 설정 관리

주요 설정:
- `CUSTOM_DOMAIN`: https://t1.sedaily.ai
- `S3_BUCKET`: nexus-title-hub-frontend
- `CLOUDFRONT_DISTRIBUTION_ID`: EIYU5SFVTHQMN
- `LAMBDA_WS_MESSAGE`: nx-tt-dev-ver3-websocket-message
- `ANTHROPIC_SECRET_NAME`: claude-opus-45-api-key

## 📝 유지보수 가이드

### 코드 업데이트 후 배포
```bash
# 프론트엔드 변경 시
./deploy-frontend.sh

# 백엔드 변경 시
./deploy-backend.sh

# 전체 배포
./deploy-main.sh
# 옵션 1 선택
```

### 환경변수 변경
1. `config/t1-production.env` 수정
2. `./update-env.sh` 실행

### 로그 확인
```bash
# Lambda 로그 실시간 확인
aws logs tail /aws/lambda/nx-tt-dev-ver3-websocket-message --follow

# 배포 로그 확인
ls -la logs/
```

## 🔍 모니터링

### CloudWatch 대시보드
- Lambda 함수 메트릭
- API Gateway 요청 수
- DynamoDB 읽기/쓰기 용량

### 비용 모니터링
- AWS Cost Explorer에서 `nx-tt-dev-ver3` 태그로 필터링

## ⚠️ 주의사항

1. **배포 전 확인**
   - AWS 계정 ID: 887078546492
   - Region: us-east-1
   - 올바른 AWS 프로필 사용 중인지 확인

2. **캐시 무효화**
   - 프론트엔드 배포 시 자동으로 CloudFront 캐시 무효화
   - 수동 무효화: `./deploy-main.sh` → 옵션 6

3. **Lambda 패키지 크기**
   - 최대 250MB (압축)
   - 현재 크기는 배포 시 표시됨

## 📞 지원
문제 발생 시 CloudWatch 로그 확인 후 담당자에게 연락