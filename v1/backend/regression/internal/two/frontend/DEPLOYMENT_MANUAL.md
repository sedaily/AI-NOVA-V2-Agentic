# Frontend 배포 매뉴얼

## 사전 준비

### 필수 도구
- Node.js 18.0 이상
- npm 또는 yarn
- AWS CLI 설치 및 설정
- Git

### 개발 환경
- VS Code 또는 WebStorm
- React Developer Tools (Chrome/Firefox 확장)
- AWS 계정 (S3, CloudFront 권한 필요)

## 1단계: 프로젝트 초기 설정

### 1.1 프로젝트 복제
```bash
git clone [repository-url] new-service-frontend
cd new-service-frontend/frontend
```

### 1.2 의존성 설치
```bash
npm install
# 또는
yarn install
```

### 1.3 환경 변수 설정
`.env.development` 파일 생성:
```
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8001
VITE_COGNITO_USER_POOL_ID=us-east-1_xxxxxxxxx
VITE_COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
VITE_AWS_REGION=us-east-1
```

`.env.production` 파일 생성:
```
VITE_API_BASE_URL=https://api.new-service.com
VITE_WS_URL=wss://ws.new-service.com
VITE_COGNITO_USER_POOL_ID=us-east-1_xxxxxxxxx
VITE_COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
VITE_AWS_REGION=us-east-1
```

### 1.4 설정 파일 수정
`src/config.js` 수정:
```javascript
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
export const WS_URL = import.meta.env.VITE_WS_URL;
export const DEFAULT_ENGINE = 'T5';
export const STORAGE_PREFIX = 'new_service_';  // 변경
```

## 2단계: 브랜딩 및 UI 커스터마이징

### 2.1 로고 및 아이콘 변경
```bash
# 파일 교체
cp new-logo.svg public/logo.svg
cp new-favicon.ico public/favicon.ico

# React 컴포넌트 수정
vi src/components/common/Header.jsx
# 로고 경로 및 alt 텍스트 변경
```

### 2.2 색상 테마 수정
`src/styles/theme.js` 수정:
```javascript
export const theme = {
  colors: {
    primary: '#007bff',     // 메인 색상
    secondary: '#6c757d',   // 보조 색상
    background: '#f8f9fa',  // 배경 색상
    text: '#212529'         // 텍스트 색상
  }
};
```

### 2.3 텍스트 및 레이블 변경
`src/constants/messages.js` 수정:
```javascript
export const MESSAGES = {
  APP_TITLE: 'New Service',
  WELCOME: 'Welcome to New Service',
  ENGINE_T5: 'Standard Model',
  ENGINE_H8: 'Premium Model'
};
```

## 3단계: API 연결 설정

### 3.1 API 엔드포인트 매핑
`src/services/api.js` 수정:
```javascript
const API_ENDPOINTS = {
  CONVERSATIONS: '/conversations',
  PROMPTS: '/prompts',
  USAGE: '/usage',
  AUTH: '/auth'
};

// Base URL 설정
axios.defaults.baseURL = API_BASE_URL;
```

### 3.2 WebSocket 연결 설정
`src/services/websocket.js` 수정:
```javascript
class WebSocketService {
  constructor() {
    this.url = WS_URL;
    this.reconnectDelay = 3000;
    this.maxReconnectAttempts = 5;
  }
  
  connect(token, conversationId) {
    const params = new URLSearchParams({
      token,
      conversationId
    });
    this.ws = new WebSocket(`${this.url}?${params}`);
  }
}
```

### 3.3 인증 설정
`src/services/auth.js` 수정:
```javascript
import { CognitoUserPool } from 'amazon-cognito-identity-js';

const poolData = {
  UserPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID,
  ClientId: import.meta.env.VITE_COGNITO_CLIENT_ID
};

export const userPool = new CognitoUserPool(poolData);
```

## 4단계: 빌드 최적화

### 4.1 Vite 설정
`vite.config.js` 수정:
```javascript
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: false,  // 프로덕션에서 소스맵 비활성화
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,  // console.log 제거
        drop_debugger: true
      }
    },
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['@mui/material', '@emotion/react'],
          utils: ['axios', 'date-fns']
        }
      }
    }
  }
});
```

### 4.2 코드 분할 적용
```javascript
// 라우트별 코드 분할
const ChatPage = lazy(() => import('./pages/ChatPage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));

// Suspense로 감싸기
<Suspense fallback={<Loading />}>
  <Routes>
    <Route path="/chat" element={<ChatPage />} />
    <Route path="/settings" element={<SettingsPage />} />
  </Routes>
</Suspense>
```

### 4.3 이미지 최적화
```bash
# 이미지 압축
npm install --save-dev imagemin imagemin-webp

# WebP 변환 스크립트
node scripts/optimize-images.js
```

## 5단계: S3 배포

### 5.1 S3 버킷 생성
```bash
# 버킷 생성
aws s3 mb s3://new-service-frontend --region us-east-1

# 정적 웹 호스팅 활성화
aws s3 website s3://new-service-frontend \
  --index-document index.html \
  --error-document index.html
```

### 5.2 버킷 정책 설정
`bucket-policy.json` 생성:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicReadGetObject",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::new-service-frontend/*"
  }]
}
```

적용:
```bash
aws s3api put-bucket-policy \
  --bucket new-service-frontend \
  --policy file://bucket-policy.json
```

### 5.3 빌드 및 업로드
```bash
# 프로덕션 빌드
npm run build

# S3 업로드
aws s3 sync dist/ s3://new-service-frontend \
  --delete \
  --cache-control "public, max-age=31536000" \
  --exclude "index.html" \
  --exclude "*.json"

# index.html은 캐시 없이
aws s3 cp dist/index.html s3://new-service-frontend/ \
  --cache-control "no-cache, no-store, must-revalidate"
```

## 6단계: CloudFront 설정

### 6.1 배포 생성
`cloudfront-config.json` 생성:
```json
{
  "CallerReference": "new-service-$(date +%s)",
  "Comment": "New Service Frontend",
  "DefaultRootObject": "index.html",
  "Origins": {
    "Items": [{
      "Id": "S3-new-service-frontend",
      "DomainName": "new-service-frontend.s3-website-us-east-1.amazonaws.com",
      "CustomOriginConfig": {
        "HTTPPort": 80,
        "HTTPSPort": 443,
        "OriginProtocolPolicy": "http-only"
      }
    }]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-new-service-frontend",
    "ViewerProtocolPolicy": "redirect-to-https",
    "Compress": true,
    "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6"
  },
  "CustomErrorResponses": {
    "Items": [{
      "ErrorCode": 404,
      "ResponseCode": 200,
      "ResponsePagePath": "/index.html",
      "ErrorCachingMinTTL": 0
    }]
  }
}
```

생성:
```bash
aws cloudfront create-distribution \
  --distribution-config file://cloudfront-config.json

# 배포 ID 저장
DISTRIBUTION_ID=[생성된 ID]
```

### 6.2 캐시 무효화
```bash
aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*"
```

### 6.3 커스텀 도메인 연결
```bash
# SSL 인증서 요청 (us-east-1 필수)
aws acm request-certificate \
  --domain-name www.new-service.com \
  --validation-method DNS \
  --region us-east-1

# CloudFront 도메인 추가
aws cloudfront update-distribution \
  --id $DISTRIBUTION_ID \
  --distribution-config file://updated-config.json
```

## 7단계: 도메인 및 DNS 설정

### 7.1 Route 53 호스팅 영역
```bash
# 호스팅 영역 생성
aws route53 create-hosted-zone \
  --name new-service.com \
  --caller-reference $(date +%s)

# 영역 ID 저장
ZONE_ID=[생성된 ID]
```

### 7.2 DNS 레코드 생성
`route53-records.json` 생성:
```json
{
  "Changes": [{
    "Action": "CREATE",
    "ResourceRecordSet": {
      "Name": "www.new-service.com",
      "Type": "A",
      "AliasTarget": {
        "DNSName": "d1234567890.cloudfront.net",
        "EvaluateTargetHealth": false,
        "HostedZoneId": "Z2FDTNDATAQYW2"
      }
    }
  }]
}
```

적용:
```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id $ZONE_ID \
  --change-batch file://route53-records.json
```

## 8단계: 환경별 배포

### 8.1 개발 환경
```bash
# 개발용 S3 버킷
aws s3 mb s3://new-service-frontend-dev

# 개발 빌드
npm run build:dev

# 배포
aws s3 sync dist/ s3://new-service-frontend-dev
```

### 8.2 스테이징 환경
```bash
# 스테이징 빌드
npm run build:staging

# CloudFront 행동 추가
aws cloudfront create-behavior \
  --distribution-id $DISTRIBUTION_ID \
  --path-pattern "/staging/*" \
  --target-origin-id "S3-staging"
```

### 8.3 프로덕션 환경
```bash
# 프로덕션 빌드
npm run build

# 블루-그린 배포
aws s3 sync dist/ s3://new-service-frontend-green
aws cloudfront update-distribution \
  --id $DISTRIBUTION_ID \
  --default-root-object index.html
```

## 9단계: 모니터링 설정

### 9.1 CloudWatch 알람
```bash
# 오류율 알람
aws cloudwatch put-metric-alarm \
  --alarm-name "Frontend-4xx-Errors" \
  --alarm-description "Alert on high 4xx error rate" \
  --metric-name 4xxErrorRate \
  --namespace AWS/CloudFront \
  --statistic Average \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold
```

### 9.2 Google Analytics 설정
`index.html` 수정:
```html
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
```

### 9.3 Sentry 에러 추적
```javascript
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: "https://xxx@sentry.io/xxx",
  environment: import.meta.env.MODE,
  tracesSampleRate: 0.1
});
```

## 10단계: 자동화 스크립트

### 10.1 통합 배포 스크립트
`deploy.sh` 생성:
```bash
#!/bin/bash
ENV=$1
DOMAIN=$2

# 환경 선택
if [ "$ENV" = "prod" ]; then
  BUCKET="new-service-frontend"
  DIST_ID="E1234567890"
else
  BUCKET="new-service-frontend-$ENV"
  DIST_ID="E0987654321"
fi

# 빌드
npm run build:$ENV

# S3 업로드
aws s3 sync dist/ s3://$BUCKET --delete

# CloudFront 무효화
aws cloudfront create-invalidation \
  --distribution-id $DIST_ID \
  --paths "/*"

echo "배포 완료: https://$DOMAIN"
```

### 10.2 실행
```bash
chmod +x deploy.sh
./deploy.sh prod www.new-service.com
```

## 성능 최적화 체크리스트

### 빌드 최적화
- Tree shaking 활성화
- 코드 분할 구현
- CSS 최소화
- 이미지 최적화 (WebP 변환)
- 폰트 최적화 (서브셋 생성)

### 네트워크 최적화
- Gzip/Brotli 압축 활성화
- HTTP/2 사용
- 리소스 프리로드
- 서비스 워커 구현

### 캐싱 전략
- 정적 자원: 1년 캐시
- index.html: 캐시 안함
- API 응답: 상황별 설정

## 트러블슈팅

### CORS 오류
```javascript
// API Gateway CORS 헤더 확인
Access-Control-Allow-Origin: https://www.new-service.com
Access-Control-Allow-Headers: Content-Type,Authorization
Access-Control-Allow-Methods: GET,POST,PUT,DELETE,OPTIONS
```

### CloudFront 403 오류
```bash
# S3 버킷 정책 확인
aws s3api get-bucket-policy --bucket new-service-frontend

# CloudFront OAI 권한 확인
aws cloudfront get-distribution --id $DISTRIBUTION_ID
```

### 라우팅 문제 (SPA)
```bash
# CloudFront 404 에러 페이지 설정
Error Code: 404
Response Code: 200
Response Page Path: /index.html
```

### 빌드 오류
```bash
# 캐시 삭제
rm -rf node_modules
rm package-lock.json
npm install

# Vite 캐시 삭제
rm -rf .vite
```

## 보안 체크리스트

### 환경 변수
- 민감한 정보 .env 파일로 분리
- .gitignore에 .env 파일 추가
- 프로덕션 환경 변수 별도 관리

### CSP 헤더
```html
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; 
               script-src 'self' 'unsafe-inline'; 
               style-src 'self' 'unsafe-inline';">
```

### HTTPS 강제
- CloudFront Viewer Protocol Policy: redirect-to-https
- HSTS 헤더 설정

### 의존성 관리
```bash
# 보안 취약점 검사
npm audit
npm audit fix

# 의존성 업데이트
npm update
```