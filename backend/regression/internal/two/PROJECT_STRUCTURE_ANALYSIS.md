# 프로젝트 구조 분석 및 리팩토링 권장사항

**분석일**: 2025-11-21
**브랜치**: refactoring-1121

## 📊 현재 프로젝트 구조

### 전체 디렉토리 크기
```
frontend/              436M (node_modules 포함)
sedaily-column-clone/  384M (전체 백업)
node_modules/          98M  (루트)
backend/               888K
infrastructure/        108K
admin-dashboard/       112K
```

---

## 🔍 주요 발견사항

### 1. ⚠️ 중복 코드 및 불필요한 파일

#### 1.1 sedaily-column-clone/ 디렉토리 (384MB)
- **문제**: 전체 프로젝트 백업이 포함되어 저장소 크기를 크게 증가
- **영향**: Git 클론 속도 저하, 저장소 크기 비대화
- **권장**: 삭제 (Git 히스토리로 충분히 버전 관리 가능)

#### 1.2 Backend 빌드 아티팩트 (여러 ZIP 파일)
```
backend/authorizer-update.zip
backend/authorizer-update2.zip
backend/conversation-complete.zip
backend/conversation-lambda-update.zip
backend/conversation_lambda.zip
backend/prompt-lambda-final.zip
backend/prompt-lambda-fix.zip
backend/prompt-lambda-update.zip
backend/usage-lambda-update.zip
```
- **문제**: 빌드된 Lambda 배포 파일들이 Git에 커밋됨
- **권장**: .gitignore에 추가 후 삭제

#### 1.3 Python 캐시 파일
```
backend/__pycache__/
backend/lib/__pycache__/
backend/services/__pycache__/
```
- **문제**: Python 바이트코드 캐시가 포함됨
- **권장**: 삭제 및 .gitignore 확인

#### 1.4 루트 node_modules/ (98MB)
- **문제**: 루트 package.json이 거의 비어있는데 node_modules가 존재
- **권장**: 불필요하면 삭제

---

### 2. 📁 디렉토리 구조

#### 현재 구조
```
sedaily_column/
├── frontend/              # React 프론트엔드
│   ├── src/
│   ├── dist/             # 빌드 출력 (배포용)
│   ├── public/
│   └── scripts/          # 배포 스크립트
├── backend/               # Python Lambda 백엔드
│   ├── handlers/         # Lambda 핸들러
│   ├── services/         # 비즈니스 로직
│   ├── lib/              # 외부 서비스 클라이언트
│   ├── src/              # 코어 로직
│   └── scripts/          # 배포 스크립트
├── admin-dashboard/       # 관리자 대시보드 (HTML)
├── infrastructure/        # AWS 인프라 설정
└── sedaily-column-clone/  # ⚠️ 전체 백업 (불필요)
```

---

### 3. 📄 문서 파일 분석

#### 루트 레벨 문서 (필요)
- ✅ `README.md` - 메인 프로젝트 문서
- ✅ `MAINTENANCE_GUIDE.md` - 유지보수 가이드
- ✅ `PROMPT_CACHING_IMPLEMENTATION.md` - 프롬프트 캐싱 구현
- ✅ `PROMPT_CACHING_PERFORMANCE.md` - 성능 분석
- ✅ `CACHING_SUMMARY.md` - 캐싱 요약
- ✅ `README_PROMPT_CACHING.md` - 캐싱 README
- ✅ `prompt-guide.md` - 프롬프트 가이드

#### Backend 문서
- ✅ `API_DEPLOYMENT_GUIDE.md`
- ✅ `API_ENDPOINTS.md`
- ✅ `API_GATEWAY_CONFIG.md`
- ✅ `API_GATEWAY_SETUP.md`
- ✅ `MULTITENANT_DEPLOYMENT_GUIDE.md`
- ✅ `MULTITENANT_STATUS.md`

#### 중복 문서 (sedaily-column-clone/)
- ⚠️ clone 디렉토리 내의 모든 문서는 중복

---

### 4. 🚀 배포 스크립트

#### 루트
- `deploy-column-frontend.sh` - 프론트엔드 배포

#### Backend Scripts
- 다양한 배포 및 설정 스크립트 (28개)
- 일부는 중복되거나 버전별로 존재

#### Frontend Scripts
- CloudFront, S3 배포 스크립트

---

## ✅ 필요한 파일/폴더

### 필수 유지
1. **frontend/** - React 앱 (소스 코드만)
2. **backend/** - Lambda 함수 (소스 코드만)
3. **infrastructure/** - AWS 인프라 설정
4. **admin-dashboard/** - 관리자 대시보드
5. **문서 파일들** - 모든 루트 레벨 MD 파일

### 조건부 유지
1. **frontend/dist/** - 빌드 결과물 (배포 전에만 필요, .gitignore 추가 권장)
2. **backend/scripts/** - 배포 스크립트 (정리 필요)

---

## 🗑️ 삭제 권장 파일/폴더

### 즉시 삭제 가능
1. ❌ `sedaily-column-clone/` - 384MB 백업 (Git으로 충분)
2. ❌ 모든 `.zip` 파일 (backend/)
3. ❌ `__pycache__/` 디렉토리들
4. ❌ 루트 `node_modules/` (필요시 재설치 가능)
5. ❌ `frontend/dist/` (빌드할 때마다 재생성됨)

### 파일 크기 절감 예상
```
Before: ~920MB
After:  ~3MB (소스 코드만)
절감률: 99.7%
```

---

## 📋 리팩토링 액션 플랜

### Phase 1: 즉시 실행 (안전)
```bash
# 1. 백업 디렉토리 삭제
rm -rf sedaily-column-clone/

# 2. Python 캐시 삭제
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# 3. ZIP 파일 삭제
rm -f backend/*.zip

# 4. 루트 node_modules 삭제 (필요시)
rm -rf node_modules/
rm -f package-lock.json
```

### Phase 2: .gitignore 업데이트
```gitignore
# Python
__pycache__/
*.py[cod]
*.so
.Python

# Build artifacts
*.zip
backend/*.zip
frontend/dist/

# Node modules
node_modules/

# Backup directories
*-clone/
*-backup/
backup*/

# OS files
.DS_Store
```

### Phase 3: 문서 정리
- 중복 문서 통합
- 오래된 가이드 제거
- README에 명확한 디렉토리 구조 명시

### Phase 4: 스크립트 정리
- 중복 배포 스크립트 통합
- 버전별 스크립트 최신 버전만 유지
- 스크립트 README 업데이트

---

## 🎯 권장 최종 구조

```
sedaily_column/
├── README.md
├── MAINTENANCE_GUIDE.md
├── .gitignore
├── package.json (최소화)
├── frontend/
│   ├── src/
│   ├── public/
│   ├── scripts/
│   ├── package.json
│   └── vite.config.js
├── backend/
│   ├── handlers/
│   ├── services/
│   ├── lib/
│   ├── src/
│   ├── utils/
│   ├── scripts/
│   └── requirements.txt
├── admin-dashboard/
│   └── *.html
├── infrastructure/
│   └── aws/
└── docs/ (선택적)
    ├── api/
    ├── deployment/
    └── caching/
```

---

## 📊 코드 품질 분석

### Frontend
- ✅ 현대적인 React 18.2 사용
- ✅ Vite 빌드 시스템
- ✅ Container-Presenter 패턴 사용
- ✅ 좋은 디렉토리 구조 (features/)

### Backend
- ✅ 명확한 레이어 분리 (handlers/services/repositories)
- ✅ Python 3.9 Lambda
- ✅ DynamoDB 레포지토리 패턴
- ⚠️ 일부 스크립트 중복

### Infrastructure
- ✅ AWS 서비스별 구성 분리
- ⚠️ IaC 도구 없음 (Terraform/CDK 권장)

---

## 🔒 보안 체크리스트

- ✅ .env 파일이 .gitignore에 포함됨
- ⚠️ backend/.env가 clone 디렉토리에 존재할 수 있음 (삭제 필요)
- ✅ API 키는 환경 변수로 관리

---

## 📈 다음 단계

1. **즉시**: Phase 1 실행 (불필요한 파일 삭제)
2. **단기**: .gitignore 업데이트 및 문서 정리
3. **중기**: 스크립트 통합 및 최적화
4. **장기**: IaC 도입 (Terraform/CDK)

---

## 💡 추가 권장사항

1. **CI/CD 파이프라인 구축**
   - GitHub Actions 또는 AWS CodePipeline
   - 자동 테스트 및 배포

2. **모노레포 도구 검토**
   - Nx, Turborepo 등 고려
   - 빌드 캐싱 및 최적화

3. **테스트 추가**
   - Frontend: Jest, React Testing Library
   - Backend: pytest, moto

4. **환경별 설정 분리**
   - dev, staging, production
   - 환경별 .env 파일

---

**분석 완료**
