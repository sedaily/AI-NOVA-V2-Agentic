# b1.sedaily.ai 도메인 설정 가이드

## 현재 설정 상태
- **CloudFront Distribution ID**: E2WPOE6AL2G5DZ
- **CloudFront Domain**: dxiownvrignup.cloudfront.net
- **Custom Domain**: b1.sedaily.ai
- **SSL Certificate**: arn:aws:acm:us-east-1:887078546492:certificate/a7029e0c-1a81-41d9-b568-d5d07ef72a58
- **S3 Bucket**: p2-two-frontend
- **Backend Stack**: p2-two

## DNS 설정 (필수)

도메인 관리 패널에서 다음 CNAME 레코드를 추가해주세요:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| CNAME | b1.sedaily.ai | dxiownvrignup.cloudfront.net | 300 |

## API 엔드포인트 (변경 없음)
- **REST API**: https://pisnqqgu75.execute-api.us-east-1.amazonaws.com/prod
- **WebSocket**: wss://dwc2m51as4.execute-api.us-east-1.amazonaws.com/prod

## 확인 방법

1. DNS 전파 확인 (5-10분 소요):
```bash
nslookup b1.sedaily.ai
dig b1.sedaily.ai
```

2. 웹사이트 접속 테스트:
```bash
curl -I https://b1.sedaily.ai
```

3. 브라우저에서 접속:
- https://b1.sedaily.ai

## 주의사항
- DNS 전파는 전 세계적으로 최대 48시간까지 걸릴 수 있습니다
- 대부분의 경우 5-30분 내에 적용됩니다
- API는 기존 AWS 도메인을 그대로 사용합니다 (커스텀 도메인 미적용)

## 문제 해결

### 사이트에 접속할 수 없는 경우
1. DNS 레코드가 올바르게 설정되었는지 확인
2. CloudFront 배포 상태 확인: `aws cloudfront get-distribution --id E2WPOE6AL2G5DZ`
3. SSL 인증서 상태 확인

### API 연결 문제
- 현재 API는 p2-two 스택을 사용합니다
- Frontend .env 파일에서 API URL이 올바른지 확인

## 기존 b1.sedaily.ai CloudFront (비활성화됨)
- Distribution ID: E1TX284N3N9KN6
- 현재 비활성화 상태이며, 완전히 삭제 가능합니다

작성일: 2025-10-07