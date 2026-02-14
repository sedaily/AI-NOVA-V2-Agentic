# 새로운 CloudFront + S3 배포 정보

## 배포 완료
생성 시간: 2025-12-04 22:54

### S3 버킷
- **버킷 이름**: buddy-frontend-202512042253
- **리전**: us-east-1
- **웹사이트 호스팅**: 활성화됨
- **Public Access**: 활성화됨

### CloudFront Distribution
- **Distribution ID**: EJX326D0QZ4T1
- **도메인**: https://d3bwe2ohfohm85.cloudfront.net
- **상태**: InProgress (배포 중 - 약 15-20분 소요)
- **Origin**: buddy-frontend-202512042253.s3.amazonaws.com

### API 엔드포인트 (b1.sedaily.ai 실제 API)
- **REST API**: https://pisnqqgu75.execute-api.us-east-1.amazonaws.com/prod
- **WebSocket**: wss://dwc2m51as4.execute-api.us-east-1.amazonaws.com/prod

## 접속 방법

### CloudFront URL (배포 완료 후)
```
https://d3bwe2ohfohm85.cloudfront.net
```

### S3 직접 접속 (테스트용)
```
http://buddy-frontend-202512042253.s3-website-us-east-1.amazonaws.com
```

### 로컬 개발 서버
```
http://localhost:3006
```

## 업데이트 방법

프론트엔드 코드 변경 후:
```bash
# 1. 빌드
cd frontend
npm run build

# 2. S3에 업로드
aws s3 sync dist/ s3://buddy-frontend-202512042253/ --delete

# 3. CloudFront 캐시 무효화 (선택사항)
aws cloudfront create-invalidation --distribution-id EJX326D0QZ4T1 --paths "/*"
```

## 주의사항
- CloudFront 배포는 전체적으로 15-20분 정도 걸립니다
- 현재 상태: InProgress (배포 진행 중)
- 배포 완료 후 https://d3bwe2ohfohm85.cloudfront.net 에서 접속 가능합니다