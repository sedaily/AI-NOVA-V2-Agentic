# 🛠 유지보수 가이드

## 📋 목차
1. [프로젝트 구조](#프로젝트-구조)
2. [자동 배포 시스템](#자동-배포-시스템)
3. [코드 수정 가이드](#코드-수정-가이드)
4. [유지보수 평가](#유지보수-평가)
5. [개선 제안사항](#개선-제안사항)

---

## 🏗 프로젝트 구조

### 백엔드 구조
```
backend/
├── handlers/           # Lambda 핸들러
│   ├── api/           # REST API 핸들러
│   └── websocket/     # WebSocket 핸들러
├── src/               # 핵심 비즈니스 로직
│   ├── models/        # 데이터 모델
│   ├── repositories/  # 데이터베이스 접근 계층
│   └── services/      # 비즈니스 로직 계층
├── lib/               # 외부 라이브러리 래퍼
├── utils/             # 유틸리티 함수
└── scripts/           # 배포 및 설정 스크립트
```

### 프론트엔드 구조
```
frontend/
├── src/
│   ├── features/      # 기능별 모듈
│   ├── shared/        # 공통 컴포넌트
│   └── config.js      # 설정 파일
└── dist/              # 빌드 결과물
```

---

## 🚀 자동 배포 시스템

### ✅ 원클릭 배포 (권장)
```bash
# 전체 배포 (프론트엔드 + 백엔드)
./deploy.sh

# 프론트엔드만 배포
./deploy.sh --frontend

# 백엔드만 배포
./deploy.sh --backend

# 캐시 무효화 없이 배포
./deploy.sh --no-cache
```

### 개별 배포 방법

#### 백엔드 배포
```bash
cd backend
./scripts/99-deploy-lambda.sh
```

#### 프론트엔드 배포
```bash
cd frontend
npm run build
aws s3 sync dist/ s3://nexus-title-hub-frontend/ --delete
```

---

## 📝 코드 수정 가이드

### 백엔드 코드 수정 시

1. **API 엔드포인트 수정**
   - 위치: `backend/handlers/api/`
   - 수정 후: `./deploy.sh --backend`

2. **비즈니스 로직 수정**
   - 위치: `backend/src/services/`
   - 수정 후: `./deploy.sh --backend`

3. **데이터베이스 스키마 변경**
   - 위치: `backend/src/models/`
   - 주의: DynamoDB 테이블 구조 변경 시 마이그레이션 필요

### 프론트엔드 코드 수정 시

1. **UI 컴포넌트 수정**
   - 위치: `frontend/src/features/`
   - 수정 후: `./deploy.sh --frontend`

2. **API 연결 설정 변경**
   - 위치: `frontend/src/config.js`
   - 수정 후: `./deploy.sh --frontend`

---

## 📊 유지보수 평가

### 🟢 잘 되어있는 부분

1. **자동화된 배포 시스템**
   - ✅ 단일 스크립트로 전체 배포 가능
   - ✅ Lambda 함수 자동 업데이트
   - ✅ CloudFront 캐시 자동 무효화

2. **모듈화된 코드 구조**
   - ✅ 계층별 분리 (MVC 패턴)
   - ✅ 서비스/리포지토리 패턴 적용
   - ✅ 재사용 가능한 컴포넌트

3. **환경 변수 관리**
   - ✅ 설정값 중앙 집중화
   - ✅ AWS 서비스별 설정 분리

### 🟡 개선 가능한 부분

1. **환경별 설정 관리**
   - 현재: 하드코딩된 값들 존재
   - 개선: `.env` 파일 활용

2. **에러 처리 및 롤백**
   - 현재: 기본적인 에러 처리만 구현
   - 개선: 자동 롤백 메커니즘 추가

3. **테스트 자동화**
   - 현재: 테스트 코드 없음
   - 개선: 단위 테스트 및 통합 테스트 추가

---

## 💡 개선 제안사항

### 1. 환경 설정 파일 추가
```bash
# .env.production 파일 생성
cat > .env.production << EOF
AWS_REGION=us-east-1
S3_BUCKET=nexus-title-hub-frontend
API_URL=https://xo9kh0vd0b.execute-api.us-east-1.amazonaws.com/prod
EOF
```

### 2. 배포 전 검증 스크립트
```bash
# validate.sh 생성
#!/bin/bash
# 1. 린트 체크
# 2. 빌드 테스트
# 3. API 연결 테스트
```

### 3. 모니터링 대시보드
- CloudWatch 대시보드 설정
- 에러 알림 설정
- 성능 메트릭 추적

### 4. CI/CD 파이프라인
- GitHub Actions 활용
- 자동 테스트 및 배포
- 브랜치별 환경 분리

---

## 📞 문제 해결

### 배포 실패 시
1. CloudWatch 로그 확인
2. `git status`로 변경사항 확인
3. `./deploy.sh --help`로 옵션 확인

### 롤백 방법
```bash
# 이전 커밋으로 롤백
git checkout HEAD~1
./deploy.sh

# 특정 버전으로 롤백
git checkout [commit-hash]
./deploy.sh
```

---

## 📈 유지보수성 점수: 7/10

### 강점
- ✅ 자동화된 배포 프로세스
- ✅ 명확한 코드 구조
- ✅ 모듈화된 아키텍처

### 개선 필요
- ⚠️ 테스트 코드 부재
- ⚠️ 환경별 설정 관리
- ⚠️ 문서화 부족

### 결론
현재 시스템은 **기본적인 유지보수는 용이**하나, 
**대규모 팀 작업이나 복잡한 기능 추가 시** 
추가적인 개선이 필요합니다.