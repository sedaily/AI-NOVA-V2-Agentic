# Nexus Multi Frontend 배포 가이드

## 📋 개요
이 디렉토리에는 Nexus Multi 프론트엔드를 AWS S3 + CloudFront로 배포하기 위한 스크립트들이 포함되어 있습니다.

## 🚀 빠른 시작

### 전체 자동 배포
```bash
chmod +x *.sh
./deploy-all.sh
```

### 단계별 수동 배포
```bash
# 1. S3 버킷 생성
./01-create-s3-bucket.sh

# 2. CloudFront 배포 생성
./02-create-cloudfront.sh

# 3. 프론트엔드 빌드 및 배포
./03-deploy-frontend.sh
```

## 📁 스크립트 설명

### 01-create-s3-bucket.sh
- 새로운 S3 버킷 생성
- 정적 웹사이트 호스팅 설정
- CORS 정책 설정
- 버전 관리 활성화

### 02-create-cloudfront.sh
- CloudFront 배포 생성
- Origin Access Control (OAC) 설정
- S3 버킷 정책 업데이트
- 캐싱 및 보안 설정

### 03-deploy-frontend.sh
- 프론트엔드 애플리케이션 빌드
- S3에 파일 업로드
- CloudFront 캐시 무효화
- 적절한 캐시 헤더 설정

## ⚙️ 사전 요구사항

### AWS CLI 설치 및 설정
```bash
# AWS CLI 설치 확인
aws --version

# AWS 자격 증명 설정
aws configure
```

### 필요한 AWS 권한
- S3: CreateBucket, PutBucketPolicy, PutObject, DeleteObject
- CloudFront: CreateDistribution, CreateInvalidation
- IAM: GetUser (계정 ID 확인용)

### Node.js 및 npm
```bash
# Node.js 버전 확인 (14.0 이상 권장)
node --version

# npm 버전 확인
npm --version
```

## 🔧 설정 변경

### S3 버킷 이름 변경
`01-create-s3-bucket.sh` 파일 수정:
```bash
BUCKET_NAME="your-custom-bucket-name"
```

### AWS 리전 변경
```bash
REGION="us-east-1"  # 원하는 리전으로 변경
```

### AWS 프로필 변경
```bash
PROFILE="your-profile"  # AWS CLI 프로필 이름
```

## 📊 배포 후 확인

### 배포 정보 확인
```bash
cat deployment-config.json
```

### CloudFront 배포 상태 확인
```bash
aws cloudfront get-distribution --id YOUR_DISTRIBUTION_ID --query 'Distribution.Status'
```

### S3 버킷 파일 확인
```bash
aws s3 ls s3://YOUR_BUCKET_NAME/
```

## 🔄 업데이트 배포

기존 배포를 업데이트하려면:
```bash
# 프론트엔드만 재배포
./03-deploy-frontend.sh
```

## 🗑️ 리소스 정리

배포한 리소스를 삭제하려면:
```bash
# CloudFront 배포 비활성화
aws cloudfront update-distribution --id YOUR_DISTRIBUTION_ID \
  --distribution-config file://disable-config.json

# CloudFront 배포 삭제 (비활성화 후)
aws cloudfront delete-distribution --id YOUR_DISTRIBUTION_ID

# S3 버킷 삭제
aws s3 rm s3://YOUR_BUCKET_NAME --recursive
aws s3api delete-bucket --bucket YOUR_BUCKET_NAME
```

## ⚠️ 주의사항

1. **비용**: CloudFront와 S3 사용에 따른 AWS 요금이 발생합니다.
2. **배포 시간**: CloudFront 배포는 완전히 활성화되는데 15-20분 정도 소요됩니다.
3. **캐시**: CloudFront 캐시 무효화는 5-10분 정도 소요됩니다.
4. **보안**: 프로덕션 환경에서는 WAF, 사용자 정의 도메인 등 추가 보안 설정을 권장합니다.

## 🔍 문제 해결

### S3 버킷 생성 실패
- 버킷 이름이 전역적으로 고유한지 확인
- AWS 권한이 충분한지 확인

### CloudFront 접근 오류
- S3 버킷 정책이 올바르게 설정되었는지 확인
- OAC 설정이 제대로 되었는지 확인

### 빌드 실패
- Node.js와 npm 버전 확인
- `npm install`로 의존성 재설치

## 📝 환경 변수 설정

프론트엔드 환경 변수는 `frontend/.env.production` 파일에서 설정:
```env
VITE_API_URL=wss://your-api.execute-api.region.amazonaws.com/stage
VITE_WS_URL=wss://your-websocket.execute-api.region.amazonaws.com/stage
VITE_ENV=production
```

## 🚦 배포 상태 모니터링

### CloudWatch 대시보드
AWS Console에서 CloudFront와 S3 메트릭 확인

### 실시간 로그
CloudFront 실시간 로그를 활성화하여 트래픽 모니터링

## 📚 추가 리소스

- [AWS S3 정적 웹사이트 호스팅 가이드](https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteHosting.html)
- [CloudFront 문서](https://docs.aws.amazon.com/cloudfront/)
- [Vite 배포 가이드](https://vitejs.dev/guide/static-deploy.html)