# W1.SEDAILY.AI Service

보도자료 AI 서비스 (w1.sedaily.ai) 소스 코드

## 🚀 Quick Start

```bash
cd w1-scripts

# 백엔드 배포 (Lambda)
./deploy-backend.sh

# 프론트엔드 배포 (React)
./deploy-frontend.sh

# 서비스 테스트
./test-service.sh

# 로그 확인
./monitor-logs.sh
```

## 📁 Structure

```
b1(bodo)/
├── w1-scripts/          # 배포 스크립트
│   ├── deploy-backend.sh
│   ├── deploy-frontend.sh
│   ├── monitor-logs.sh
│   └── test-service.sh
├── backend/             # Lambda 코드
├── frontend/            # React 앱
└── config/              # 설정 파일
```

## 🔑 Configuration

- **API Key**: AWS Secrets Manager `bodo-v1`
- **Model**: Claude 4.5 Opus (`claude-opus-4-5-20251101`)
- **Domain**: https://w1.sedaily.ai

## 📝 Notes

- w1.sedaily.ai 서비스 전용
- 다른 서비스 (b1, g2, nx) 무시
- 모든 스크립트는 w1-scripts/ 폴더에 있음

자세한 내용: [w1-scripts/README.md](w1-scripts/README.md)