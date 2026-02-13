# nexus-template-p2 프로젝트 구조 분석

## 📊 전체 구조 개요

```
nexus-template-p2/
├── backend/              # 956KB - Python Lambda 백엔드
├── frontend/             # 437MB - React 프론트엔드 (node_modules 포함)
├── scripts/              # 404KB - 레거시 배포 스크립트 (56개 파일)
├── scripts-v2/           # 432KB - 개선된 배포 스크립트
├── pro-sol/              # 문제 해결 문서
└── [문서 및 설정 파일들]
```

## 🔍 코드 구성 상세

### 1. Backend (Python - 31개 파일)

#### 📁 핵심 코드 (src/)
```
src/
├── config/
│   ├── __init__.py
│   ├── aws.py              # AWS 서비스 설정
│   └── database.py         # DynamoDB 설정
├── models/
│   ├── conversation.py     # 대화 모델
│   ├── prompt.py          # 프롬프트 모델
│   └── usage.py           # 사용량 모델
├── repositories/
│   ├── conversation_repository.py
│   ├── prompt_repository.py
│   └── usage_repository.py
└── services/
    ├── conversation_service.py
    ├── prompt_service.py
    └── usage_service.py
```

#### 📁 Lambda 핸들러
```
handlers/
├── api/
│   ├── conversation.py    # 대화 CRUD API
│   ├── prompt.py         # 프롬프트 CRUD API
│   └── usage.py          # 사용량 조회 API
└── websocket/
    ├── connect.py         # WebSocket 연결
    ├── disconnect.py      # WebSocket 연결 해제
    ├── message.py         # 메시지 처리
    └── conversation_manager.py
```

#### 📁 외부 서비스 클라이언트
```
lib/
├── bedrock_client_enhanced.py  # AWS Bedrock (Claude) 클라이언트
└── perplexity_client.py        # Perplexity 웹 검색
```

#### 📁 유틸리티
```
utils/
├── logger.py              # 로깅 설정
└── response.py            # API 응답 포맷
```

#### 📁 서비스 레이어
```
services/
├── websocket_service.py         # 현재 사용 중 ✅
├── websocket_service_backup.py  # 백업 (삭제 가능)
└── websocket_service_fixed.py   # 백업 (삭제 가능)
```

### 2. Frontend (React + Vite)

#### 📁 기능별 구조 (features/)
```
features/
├── auth/                  # 인증 (로그인/회원가입)
│   ├── components/
│   ├── containers/
│   ├── hooks/
│   ├── presenters/
│   └── services/
├── chat/                  # 실시간 채팅
│   ├── components/
│   ├── containers/
│   ├── hooks/
│   ├── presenters/
│   ├── services/
│   └── styles/
├── dashboard/             # 대시보드 & 프롬프트 관리
│   ├── components/
│   ├── containers/
│   ├── hooks/
│   ├── presenters/
│   └── services/
├── landing/               # 랜딩 페이지
├── profile/               # 프로필 페이지
└── subscription/          # 구독 페이지
```

#### 📁 공유 컴포넌트
```
shared/
├── components/
│   ├── layout/
│   │   ├── Header.jsx
│   │   └── Sidebar.jsx
│   └── ui/
│       └── PageTransition.jsx
└── utils/
    └── promptService.js
```

### 3. 배포 스크립트

#### scripts/ (레거시 - 56개 파일)
```
00-config.sh
01-create-dynamodb.sh
02-create-lambda-functions.sh
03-setup-rest-api.sh
04-setup-websocket-api.sh
...
99-fix-all-issues.sh
```

#### scripts-v2/ (개선 버전)
```
01-deploy-dynamodb.sh
02-deploy-lambda.sh
03-deploy-api-gateway-final.sh
04-update-config.sh
05-deploy-lambda-code-improved.sh
06-deploy-frontend.sh
deploy-all.sh
```

## ⚠️ 불필요하거나 중복된 파일/폴더

### 🗑️ 즉시 삭제 가능

#### 1. Backend 백업 디렉토리 (6개)
```
backend/backup_20250926_093031/     # 9월 26일 백업
backend/backup_20250926_093814/     # 9월 26일 백업
backend/backup_20250926_093928/     # 9월 26일 백업
backend/backup_20250926_102143/     # 9월 26일 백업
backend/backup_20250926_132649/     # 9월 26일 백업
backend/backup_20251115_094456/     # 11월 15일 백업
```
**이유**: Git으로 버전 관리 중이므로 백업 불필요

#### 2. 중복 WebSocket 서비스 파일
```
backend/services/websocket_service_backup.py
backend/services/websocket_service_fixed.py
```
**이유**: `websocket_service.py`만 사용 중

#### 3. 대용량 ZIP 파일 (15MB)
```
websocket-service-complete.zip      # 15MB
websocket-service-model-fix.zip     # 1.4KB
backend/lambda-deployment.zip        # 68KB (최근 배포용)
```
**이유**: Git으로 관리되므로 압축 파일 불필요

#### 4. Frontend 백업 .env 파일
```
frontend/.env.backup.20250924_224814
frontend/.env.backup.20250925_002827
frontend/.env.backup.20250926_164009
frontend/.env.production.backup.20250926_164009
frontend/.env.w1
```
**이유**: 템플릿 파일로 충분, 보안상 .env는 Git에서 제외

#### 5. 레거시 스크립트 디렉토리
```
scripts/  (56개 파일, 404KB)
```
**이유**: scripts-v2로 개선되었으며, 더 이상 사용하지 않음

#### 6. 임시/테스트 스크립트 (루트)
```
add-conversation-methods.sh
fix-conversation-api.sh
force-lambda-restart.sh
setup-prompt-routes.sh
setup-usage-api.sh
update-lambda-integration.sh
```
**이유**: 일회성 설정 스크립트, 이미 적용됨

#### 7. 레거시 파일들
```
w1-api-swagger.json                 # W1 서비스용 (현재 B1/P2 사용)
endpoints.json                       # 정적 엔드포인트 정보
endpoints.txt                        # 중복
api-routes.yaml                      # 문서화용
```

#### 8. 테스트 파일
```
backend/test_prompt_caching.py      # 개발 테스트 파일
```

### 📦 .gitignore 추가 권장

현재 추적되고 있는 불필요한 파일들:
```
# Python
__pycache__/
*.pyc
*.pyo
*.egg-info/

# Deployment
*.zip
lambda-deployment.zip

# Environment
.env
.env.*
!.env.template
!.env.production.template

# Backups
backup_*/
*.backup

# Logs
*.log
deployment-log.txt
deployment-info.txt

# IDE
.vscode/
.idea/

# OS
.DS_Store
```

## 📊 디스크 사용량 분석

```
전체 프로젝트: ~438MB
├── frontend/node_modules: ~430MB (필수)
├── backend: ~1MB
├── scripts: ~400KB (삭제 가능)
├── scripts-v2: ~400KB (유지)
├── 백업 디렉토리: ~200KB (삭제 가능)
└── ZIP 파일: ~15MB (삭제 가능)
```

**삭제 후 예상 절감**: ~16MB

## ✅ 유지해야 할 핵심 구조

### Backend
```
backend/
├── handlers/           ✅ Lambda 함수 핸들러
├── lib/               ✅ 외부 서비스 클라이언트
├── services/          ✅ 비즈니스 로직
├── src/
│   ├── config/       ✅ 설정
│   ├── models/       ✅ 데이터 모델
│   ├── repositories/ ✅ DB 접근 계층
│   └── services/     ✅ 서비스 계층
├── utils/            ✅ 유틸리티
├── .env.template     ✅ 환경변수 템플릿
└── requirements.txt  ✅ Python 의존성
```

### Frontend
```
frontend/
├── src/
│   ├── features/     ✅ 기능별 모듈
│   ├── shared/       ✅ 공유 컴포넌트
│   ├── App.jsx       ✅ 루트 컴포넌트
│   ├── main.jsx      ✅ 엔트리 포인트
│   ├── config.js     ✅ 설정
│   └── index.css     ✅ 글로벌 스타일
├── public/           ✅ 정적 파일
├── .env.template     ✅ 환경변수 템플릿
├── package.json      ✅ 의존성
├── vite.config.js    ✅ Vite 설정
└── tailwind.config.js ✅ Tailwind 설정
```

### 배포
```
scripts-v2/           ✅ 개선된 배포 스크립트
deploy-service.sh     ✅ 메인 배포 스크립트
deploy-p2-frontend.sh ✅ 프론트엔드 배포
deploy.sh             ✅ 간단 배포
```

### 문서
```
README.md                        ✅ 프로젝트 개요
DEPLOYMENT_GUIDE.md              ✅ 배포 가이드
CACHING_SUMMARY.md               ✅ 캐싱 구현
CLOUDWATCH_LOGS_GUIDE.md         ✅ 모니터링
B1_DOMAIN_SETUP.md               ✅ 도메인 설정
LOGIN_SIGNUP_UPDATE_GUIDE.md     ✅ 인증 가이드
PROMPT_CACHING_PERFORMANCE.md    ✅ 성능 분석
```

## 🎯 권장 리팩토링 작업

### 1. 즉시 실행 (안전)
```bash
# 백업 디렉토리 삭제
rm -rf backend/backup_*

# 중복 서비스 파일 삭제
rm backend/services/websocket_service_backup.py
rm backend/services/websocket_service_fixed.py

# ZIP 파일 삭제
rm *.zip
rm backend/*.zip

# 백업 .env 파일 삭제
rm frontend/.env.backup.*
rm frontend/.env.production.backup.*
rm frontend/.env.w1
```

### 2. 검토 후 삭제 (주의)
```bash
# 레거시 스크립트 (scripts-v2로 대체 확인 후)
rm -rf scripts/

# 임시 스크립트들 (이미 적용 확인 후)
rm add-conversation-methods.sh
rm fix-conversation-api.sh
rm force-lambda-restart.sh
rm setup-prompt-routes.sh
rm setup-usage-api.sh
rm update-lambda-integration.sh

# 레거시 파일들
rm w1-api-swagger.json
rm endpoints.json
rm endpoints.txt
```

### 3. .gitignore 업데이트
```bash
# .gitignore에 추가
echo "
# Python
__pycache__/
*.pyc
backup_*/

# Deployment
*.zip
deployment-log.txt
deployment-info.txt

# Environment
.env
.env.*
!.env.template
!.env.production.template
" >> .gitignore
```

## 📈 코드 품질 개선 제안

### 1. Backend 구조
- ✅ 계층 분리가 잘 되어 있음 (Controller → Service → Repository)
- ✅ DDD 패턴 적용
- ⚠️ 테스트 코드 없음 → pytest 도입 권장

### 2. Frontend 구조
- ✅ Feature-based 아키텍처
- ✅ Presentational/Container 패턴
- ⚠️ 타입 체크 없음 → TypeScript 마이그레이션 고려

### 3. 문서화
- ✅ 배포/설정 문서 잘 작성됨
- ⚠️ API 문서 없음 → OpenAPI/Swagger 추가 권장
- ⚠️ 코드 주석 부족 → Docstring 추가 권장

## 🎯 최종 요약

### 필수 유지 (핵심 코드)
- `backend/handlers/`, `lib/`, `services/`, `src/` - Lambda 백엔드
- `frontend/src/` - React 프론트엔드
- `scripts-v2/` - 배포 스크립트
- 주요 문서 파일들

### 삭제 권장 (~16MB 절감)
- ❌ 백업 디렉토리 6개
- ❌ 중복 서비스 파일 2개
- ❌ ZIP 파일 3개
- ❌ 백업 .env 파일 5개
- ❌ 레거시 scripts/ 디렉토리
- ❌ 임시 스크립트 6개

### 개선 제안
1. 테스트 코드 추가
2. TypeScript 도입
3. API 문서화
4. CI/CD 파이프라인 구축
