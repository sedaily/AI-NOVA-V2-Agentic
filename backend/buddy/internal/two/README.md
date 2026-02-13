# sed-nexus-buddy

P2 서비스 - Claude 4.5 Opus Direct API 통합 프로젝트

## 📋 주요 문서

- [Claude 4.5 Opus 마이그레이션 가이드](./CLAUDE_45_OPUS_MIGRATION_GUIDE.md) - AWS Bedrock에서 Claude Direct API로 전환

## 🚀 Quick Start

1. AWS Secrets Manager에 API 키 설정 (`buddy-v1`)
2. Lambda 환경변수 업데이트  
3. 코드 배포

자세한 내용은 마이그레이션 가이드를 참조하세요.

## 📁 프로젝트 구조

```
.
├── backend/           # Lambda 함수 및 서버 코드
│   ├── handlers/      # API & WebSocket 핸들러
│   ├── lib/          # AI 클라이언트 (Anthropic, Bedrock, Perplexity)
│   └── services/     # 비즈니스 로직
├── frontend/          # React 프론트엔드
├── scripts/           # 배포 스크립트
├── scripts-v2/        # 개선된 배포 스크립트
└── docs/archive/      # 이전 문서 보관
```

## 🔧 주요 설정

- **AI Model**: Claude 4.5 Opus (`claude-opus-4-5-20251101`)
- **Region**: us-east-1
- **Secret**: `buddy-v1`

## 📞 문의

서울경제신문 AI 개발팀