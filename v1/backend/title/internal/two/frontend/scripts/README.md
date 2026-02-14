# Frontend Scripts

프론트엔드 AWS 리소스 설정 및 배포 스크립트 모음

## 📁 스크립트 구조

```
scripts/
├── 01-setup-cloudfront.sh    # CloudFront 배포 생성
├── 02-setup-s3-policy.sh     # S3 버킷 정책 설정
└── 99-deploy-frontend.sh     # Frontend 빌드 & 배포
```

## 🚀 실행 순서

### 1️⃣ 초기 설정 (최초 1회)
```bash
# CloudFront 배포 생성
./01-setup-cloudfront.sh

# S3 버킷 정책 업데이트
./02-setup-s3-policy.sh
```

### 2️⃣ 배포 (코드 변경 시마다)
```bash
# 빌드 & S3 업로드 & CloudFront 캐시 무효화
./99-deploy-frontend.sh
```

## 📝 스크립트 설명

### `01-setup-cloudfront.sh`
- **용도**: CloudFront 배포 생성
- **설정**:
  - Origin: S3 버킷
  - HTTPS 리다이렉션
  - SPA 라우팅 (404 → index.html)

### `02-setup-s3-policy.sh`
- **용도**: S3 버킷 공개 읽기 정책 설정
- **정책**: 정적 웹사이트 호스팅 활성화

### `99-deploy-frontend.sh`
- **용도**: Frontend 배포 자동화
- **프로세스**:
  1. S3 버킷 확인/생성
  2. 빌드 파일 업로드
  3. CloudFront 캐시 무효화
- **특징**:
  - 자동 캐시 설정
  - index.html no-cache
  - 기타 파일 장기 캐시

## 📋 설정 값

### S3 버킷
- **이름**: `nexus-title-hub-frontend`
- **리전**: `us-east-1`

### CloudFront
- **Distribution ID**: `EIYU5SFVTHQMN`
- **URL**: https://d1s58eamawxu4.cloudfront.net

## ⚠️ 주의사항

1. **빌드 필수**
   ```bash
   npm run build
   ```

2. **환경 변수 확인**
   ```bash
   # .env 파일 필요
   cat .env
   ```

3. **AWS 권한 필요**
   - S3 버킷 관리
   - CloudFront 배포 관리

## 🔧 문제 해결

### 빌드 실패
```bash
npm install
npm run build
```

### 배포 권한 오류
```bash
chmod +x scripts/*.sh
```

### 캐시 문제
```bash
# CloudFront 수동 무효화
aws cloudfront create-invalidation \
  --distribution-id EIYU5SFVTHQMN \
  --paths "/*"
```

## 🔗 접속 URL

- **CloudFront**: https://d1s58eamawxu4.cloudfront.net
- **S3 Direct**: http://nexus-title-hub-frontend.s3-website-us-east-1.amazonaws.com