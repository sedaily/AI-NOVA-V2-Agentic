# B1.SEDAILY.AI 배포 스크립트

## 서비스 정보
- 도메인: b1.sedaily.ai
- REST API: p2-two-api (pisnqqgu75)
- WebSocket API: p2-two-websocket (dwc2m51as4)
- Lambda Functions: p2-two-* (6개)

## 스크립트 목록

### 1. deploy-backend.sh
백엔드 Lambda 코드를 패키징하고 배포합니다.

### 2. deploy-frontend.sh
프론트엔드를 빌드하고 S3에 배포합니다.

### 3. deploy-all.sh
전체 서비스를 배포합니다.

### 4. update-env.sh
Lambda 환경변수를 업데이트합니다.

## 사용 방법

```bash
# 백엔드만 배포
./deploy-backend.sh

# 프론트엔드만 배포
./deploy-frontend.sh

# 전체 배포
./deploy-all.sh
```