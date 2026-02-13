# 로그인/회원가입 페이지 업데이트 가이드

## 개요
nexus_완성템플릿_로그인o 프로젝트의 로그인/회원가입 디자인을 다른 프로젝트에 적용하는 반복 작업 가이드입니다.

## 디자인 특징

### 소스 프로젝트: nexus_완성템플릿_로그인o
- **배경**: 고정 라이트 그레이 그라디언트 `linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)`
- **펜 일러스트레이션**: 550x550px (로그인), 900x900px (회원가입), opacity 0.12
- **로고 크기**: 56x56px (로그인), 48x48px (회원가입)
- **색상**: 고정 색상 값 사용 (CSS 변수 사용 안 함)
- **필터**: `grayscale(100%) contrast(1.15) brightness(0.95)`

### 주요 차이점
❌ **사용하지 않는 스타일** (nexus-template-v2):
- HSL CSS 변수: `hsl(var(--bg-100))`
- 작은 펜: 128x128px, opacity 0.03
- 작은 로고: 14x14px

✅ **사용하는 스타일** (nexus_완성템플릿_로그인o):
- 고정 색상: `#f8f9fa`, `#e9ecef`
- 큰 펜: 550x550px, opacity 0.12
- 큰 로고: 56x56px

---

## 작업 단계

### 1단계: 소스 파일 위치 확인
```bash
# 소스 프로젝트 경로
SOURCE_PROJECT="/Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/Nexus_first_title/nexus_완성템플릿_로그인o/frontend"

# 복사할 파일들
LOGIN_PRESENTER="$SOURCE_PROJECT/src/features/auth/presenters/LoginPresenter.jsx"
SIGNUP_PAGE="$SOURCE_PROJECT/src/features/auth/components/SignUpPage.jsx"
PEN_IMAGES="$SOURCE_PROJECT/public/images/illustrations/pen*.png"
```

### 2단계: 대상 프로젝트에 파일 복사

#### 프로젝트별 경로 매핑

| 프로젝트 | 경로 | 도메인 | S3 버킷 | CloudFront ID |
|---------|------|--------|---------|---------------|
| nexus-template-p2 | `/Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/Prodction/nuexus_temple/nexus-template-p2` | b1.sedaily.ai | p2-two-frontend | E2WPOE6AL2G5DZ |
| nexus-template-v2 | `/Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/Prodction/nuexus_temple/nexus-template-v2` | t1.sedaily.ai | p1-frontend | E3UHFUE0KPY0PZ |
| production-frontend | `/Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/Prodction/nuexus_temple/production-frontend` | p1.sedaily.ai | production-sedaily-frontend | E33UUH9S1ND62A |
| w1 (bodo) | `/Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/Prodction/nuexus_temple/b1(bodo)/frontend` | w1.sedaily.ai | w1-frontend | E10S6CKR5TLUBG |
| f1 (first_nexux) | `/Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/Prodction/nuexus_temple/first_nexux/frontend` | f1.sedaily.ai | f1-frontend | E31CIS8NDSQNVV |

#### 복사 명령어 템플릿
```bash
# TARGET_PROJECT를 위 테이블에서 선택
TARGET_PROJECT="[대상 프로젝트 경로]"

# 1. LoginPresenter.jsx 복사
cp "/Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/Nexus_first_title/nexus_완성템플릿_로그인o/frontend/src/features/auth/presenters/LoginPresenter.jsx" \
   "$TARGET_PROJECT/frontend/src/features/auth/presenters/LoginPresenter.jsx"

# 2. SignUpPage.jsx 복사
cp "/Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/Nexus_first_title/nexus_완성템플릿_로그인o/frontend/src/features/auth/components/SignUpPage.jsx" \
   "$TARGET_PROJECT/frontend/src/features/auth/components/SignUpPage.jsx"

# 3. 펜 일러스트레이션 이미지 복사 (이미 있는 경우 스킵 가능)
cp /Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/Nexus_first_title/nexus_완성템플릿_로그인o/frontend/public/images/illustrations/pen*.png \
   "$TARGET_PROJECT/frontend/public/images/illustrations/
```

### 3단계: 빌드 및 배포

#### nexus-template-p2 (b1.sedaily.ai)
```bash
cd /Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/Prodction/nuexus_temple/nexus-template-p2
bash deploy-p2-frontend.sh
```

#### nexus-template-v2 (t1.sedaily.ai)
```bash
cd /Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/Prodction/nuexus_temple/nexus-template-v2
bash deploy-frontend.sh
```

#### production-frontend (p1.sedaily.ai)
```bash
cd /Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/Prodction/nuexus_temple/production-frontend
bash deploy-production-frontend.sh
```

#### w1 (w1.sedaily.ai)
```bash
cd /Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/Prodction/nuexus_temple/b1\(bodo\)/frontend
bash scripts/update-w1-frontend.sh
```

#### f1 (f1.sedaily.ai)
```bash
cd /Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/Prodction/nuexus_temple/first_nexux/frontend
bash scripts/deploy-f1-frontend.sh
```

### 4단계: 배포 확인
- CloudFront 캐시 무효화 완료 대기 (2-3분)
- 브라우저 캐시 클리어 (Cmd+Shift+R)
- 로그인/회원가입 페이지 확인

#### 확인 사항
✅ 배경이 라이트 그레이 그라디언트인지
✅ 펜 일러스트레이션이 크게 보이는지 (희미하게)
✅ 로고가 크게 보이는지
✅ 버튼이 3색 그라디언트인지

---

## 빠른 작업 스크립트

### 전체 프로젝트 일괄 업데이트
```bash
#!/bin/bash

SOURCE="/Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/Nexus_first_title/nexus_완성템플릿_로그인o/frontend"

# 프로젝트 배열
declare -a PROJECTS=(
  "/Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/Prodction/nuexus_temple/nexus-template-p2"
  "/Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/Prodction/nuexus_temple/nexus-template-v2"
  "/Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/Prodction/nuexus_temple/production-frontend"
  "/Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/Prodction/nuexus_temple/b1(bodo)/frontend"
  "/Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/Prodction/nuexus_temple/first_nexux/frontend"
)

for PROJECT in "${PROJECTS[@]}"; do
  echo "📦 업데이트 중: $PROJECT"

  # LoginPresenter.jsx 복사
  cp "$SOURCE/src/features/auth/presenters/LoginPresenter.jsx" \
     "$PROJECT/frontend/src/features/auth/presenters/LoginPresenter.jsx" 2>/dev/null || \
  cp "$SOURCE/src/features/auth/presenters/LoginPresenter.jsx" \
     "$PROJECT/src/features/auth/presenters/LoginPresenter.jsx"

  # SignUpPage.jsx 복사
  cp "$SOURCE/src/features/auth/components/SignUpPage.jsx" \
     "$PROJECT/frontend/src/features/auth/components/SignUpPage.jsx" 2>/dev/null || \
  cp "$SOURCE/src/features/auth/components/SignUpPage.jsx" \
     "$PROJECT/src/features/auth/components/SignUpPage.jsx"

  echo "✅ 완료: $PROJECT"
done

echo ""
echo "🎉 모든 프로젝트 파일 업데이트 완료!"
echo "⚠️  각 프로젝트별로 배포 스크립트를 실행하세요."
```

---

## 주의사항

1. **펜 이미지 경로**: `/images/illustrations/pen1.png ~ pen4.png` 경로가 올바른지 확인
2. **로고 이미지**: `/images/ainova.png` 파일이 존재하는지 확인
3. **CloudFront 캐시**: 배포 후 반드시 2-3분 대기
4. **브라우저 캐시**: 하드 리프레시 (Cmd+Shift+R) 필수

---

## 배포 이력

| 날짜 | 프로젝트 | 도메인 | 작업자 | 비고 |
|------|---------|--------|--------|------|
| 2025-11-04 14:51 | nexus-template-p2 | b1.sedaily.ai | Claude | 초기 배포 |

---

## 문제 해결

### 배경색이 적용되지 않음
- HSL 변수 대신 고정 색상 코드 사용 확인
- LoginPresenter.jsx 파일이 올바른 소스에서 복사되었는지 확인

### 펜 이미지가 보이지 않음
- public/images/illustrations/ 경로에 pen1~pen4.png 파일 확인
- S3에 이미지가 업로드되었는지 확인

### 캐시 문제
```bash
# CloudFront 캐시 무효화
aws cloudfront create-invalidation \
  --distribution-id [CLOUDFRONT_ID] \
  --paths "/*"
```

---

## 참고 링크

- 소스 프로젝트: `/Users/yeong-gwang/Documents/work/서울경제신문/DEV/Sedailyio/Nexus_first_title/nexus_완성템플릿_로그인o`
- 배포된 도메인:
  - b1.sedaily.ai (nexus-template-p2)
  - t1.sedaily.ai (nexus-template-v2)
  - p1.sedaily.ai (production-frontend)
  - w1.sedaily.ai (bodo)
  - f1.sedaily.ai (first_nexux)
