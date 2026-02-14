# Bodo Frontend 배포 가이드

## 📋 사전 요구사항

1. AWS CLI 설치 및 설정
```bash
aws configure
# AWS Access Key ID 입력
# AWS Secret Access Key 입력
# Default region: ap-northeast-2 (서울)
# Default output format: json
```

2. Node.js 18+ 설치
3. jq 설치 (JSON 파싱용)
```bash
brew install jq  # macOS
```

## 🚀 방법 1: Shell 스크립트를 사용한 배포 (권장)

### 초기 배포
```bash
cd frontend/deploy
chmod +x cloudfront-deploy.sh
./cloudfront-deploy.sh
```

### 업데이트 배포
```bash
cd frontend/deploy
chmod +x update-deployment.sh
./update-deployment.sh
```

## 🏗️ 방법 2: AWS CDK를 사용한 배포

### CDK 설치 및 초기 설정
```bash
npm install -g aws-cdk
cd infrastructure/cdk
npm install
```

### CDK 배포
```bash
# 프론트엔드 빌드 먼저 실행
cd ../../frontend
npm run build

# CDK 배포
cd ../infrastructure/cdk
npm run build
cdk bootstrap  # 처음 한 번만 실행
cdk deploy
```

### CDK 스택 삭제
```bash
cdk destroy
```

## 📁 프로젝트 구조

```
bodo/
├── frontend/               # React 프론트엔드
│   ├── src/               # 소스 코드
│   ├── dist/              # 빌드 결과물
│   └── deploy/            # 배포 스크립트
│       ├── cloudfront-deploy.sh     # 초기 배포 스크립트
│       ├── update-deployment.sh     # 업데이트 스크립트
│       └── deployment-info.json     # 배포 정보 (자동 생성)
│
└── infrastructure/        # 인프라 코드
    └── cdk/              # AWS CDK
        ├── lib/          # CDK 스택 정의
        ├── bin/          # CDK 앱 엔트리
        └── package.json  # 의존성

```

## 🔧 환경 변수 설정

프론트엔드에서 사용할 환경 변수는 `.env` 파일에 설정:

```bash
# frontend/.env.production
VITE_API_BASE_URL=https://api.example.com
VITE_WS_URL=wss://ws.example.com
```

## 📊 배포 정보 확인

배포 후 `frontend/deploy/deployment-info.json` 파일에서 확인:
```json
{
  "bucketName": "bodo-frontend-xxx",
  "cloudFrontId": "E1234567890ABC",
  "cloudFrontDomain": "d1234567890.cloudfront.net",
  "region": "ap-northeast-2"
}
```

## 🔄 CI/CD 파이프라인 (GitHub Actions)

`.github/workflows/deploy.yml` 파일 생성:

```yaml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
          
      - name: Build
        run: |
          cd frontend
          npm run build
          
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-northeast-2
          
      - name: Deploy to S3
        run: |
          aws s3 sync frontend/dist/ s3://${{ secrets.S3_BUCKET }}/ --delete
          
      - name: Invalidate CloudFront
        run: |
          aws cloudfront create-invalidation \
            --distribution-id ${{ secrets.CLOUDFRONT_ID }} \
            --paths "/*"
```

## 🛠️ 트러블슈팅

### 1. S3 버킷 이름 충돌
- 버킷 이름은 전 세계적으로 고유해야 함
- 스크립트가 자동으로 타임스탬프와 랜덤 문자열 추가

### 2. CloudFront 배포 지연
- 초기 배포는 15-20분 소요
- 캐시 무효화는 5-10분 소요

### 3. CORS 에러
- API 서버에서 CloudFront 도메인 허용 필요
- CloudFront 배포 설정에서 헤더 전달 설정

### 4. 권한 오류
- AWS IAM 사용자에 다음 권한 필요:
  - S3FullAccess
  - CloudFrontFullAccess
  - IAMReadOnlyAccess (OAI 생성용)

## 📞 지원

문제가 발생하면:
1. deployment-info.json 파일 확인
2. AWS Console에서 CloudFront/S3 상태 확인
3. 브라우저 개발자 도구 콘솔 확인