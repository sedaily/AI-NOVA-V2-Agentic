# NOVA v3 Phase별 프롬프트 매핑

## 개요

프론트엔드 파이프라인 Phase와 백엔드 Agent 프롬프트 간의 매핑을 정의합니다.

---

## 1차 분류: Agent별

```
prompts/
├── 01_supervisor_full.txt     → Supervisor Agent (총괄)
├── 02_detector_full.txt       → Detector Agent (분석)
├── 03_writer_full.txt         → Writer Agent (작성)
├── 04_quality_full.txt        → Quality Agent (교열/퇴고)
├── 05_title_full.txt          → Title Agent (제목)
└── 06_translation_full.txt    → Translation Agent (번역)
```

---

## 2차 분류: Phase별 (파이프라인 단계)

### Phase 0: Home (홈)
- **화면**: HomeView.jsx
- **기능**: 모드 선택 (단계별 / 자동)
- **Agent**: 없음 (UI만)

---

### Phase 1: 소재 입력 (Source Input)
- **화면**: Phase1View.jsx
- **기능**: 보도자료/소재 텍스트 입력
- **Agent**: 없음 (입력만)
- **다음 단계**: Phase 2로 전달

---

### Phase 2: 소재 분석 (Analysis)
- **화면**: Phase2View.jsx
- **기능**: 5W1H 추출, 앵글 후보 도출, 뉴스가치 평가
- **Agent**: **Detector Agent**
- **프롬프트**:
  - `02_detector_full.txt` (W_prompts STEP1)
- **KB**:
  - `kb/writer_kb.txt` (분야별 분석 모듈)
- **API**: `/v3/analyze`
- **출력**:
  ```json
  {
    "angles": ["앵글1", "앵글2", "앵글3"],
    "summary": "핵심 요약",
    "newsValue": "뉴스가치 평가"
  }
  ```

---

### Phase 3: 초안 작성 (Draft Generation)
- **화면**: Phase3View.jsx
- **기능**: 선택된 앵글 기반 기사 초안 생성
- **Agent**: **Writer Agent**
- **프롬프트**:
  - `03_writer_full.txt` (W_prompts STEP2-5)
- **KB**:
  - `kb/writer_kb.txt` (확장 모듈)
- **API**: `/v3/draft`
- **출력**:
  ```json
  {
    "draft": "기사 초안 전문",
    "wordCount": 1200,
    "angle": "선택된 앵글"
  }
  ```

---

### Phase 4: 교열/퇴고 (Proofread & Revise)
- **화면**: Phase4View.jsx
- **기능**: 맞춤법/문법 교정 + 문체/구조 개선
- **Agent**: **Quality Agent**
- **프롬프트**:
  - `04_quality_full.txt`
    - PART 1: P_prompts (교열)
    - PART 2: R_prompts (퇴고)
- **KB**:
  - `kb/quality_proofread_kb.txt` (P_files - KB 레지스트리)
  - `kb/quality_revise_kb.txt` (R_files - 스타일북)
- **API**: `/v3/proofread`, `/v3/revise`
- **자동 선택**:
  - 1,000자 미만 → C1 (숏폼 임팩트)
  - 1,000자 이상 → C2 (롱폼 구조)
- **출력**:
  ```json
  {
    "corrected": "교열된 텍스트",
    "corrections": [{"원문": "수정", "사유": "이유"}],
    "revised": "퇴고된 텍스트",
    "readabilityScore": 85
  }
  ```

---

### Phase 5: 제목 생성 (Title Generation)
- **화면**: Phase5View.jsx
- **기능**: TITLE-NOMICS 3.0으로 창의적 제목 생성
- **Agent**: **Title Agent**
- **프롬프트**:
  - `05_title_full.txt` (T_prompts - TITLE-NOMICS 3.0)
- **KB**:
  - `kb/title_kb.txt` (T_files - 창의성 DNA 엔진)
- **API**: `/v3/titles`
- **출력**:
  ```json
  {
    "titles": [
      {"title": "제목1", "type": "S+급", "creativity": 95},
      {"title": "제목2", "type": "S급", "creativity": 90},
      ...
    ]
  }
  ```

---

### Phase 6: 완료 (Completion)
- **화면**: CompletionView.jsx
- **기능**: 최종 기사 확인, 저장, 복사
- **Agent**: 없음 (결과 표시만)

---

## 자동 모드 (Auto Write)

### AutoWrite Phase
- **화면**: AutoWriteView.jsx
- **기능**: 소재 입력 → 완성 기사 (원스톱)
- **Agent**: **Supervisor Agent** (조율)
- **프롬프트**: `01_supervisor_full.txt`
- **파이프라인**:
  ```
  Supervisor
      ↓
  Detector (Phase 2) → Writer (Phase 3) → Quality (Phase 4) → Title (Phase 5)
      ↓
  완성된 기사 + 제목
  ```
- **API**: `/v3/auto`

---

## 번역 모드 (Translation)

### Translation Phase
- **화면**: (별도 구현 필요)
- **기능**: 일본어/영어 기사 번역
- **Agent**: **Translation Agent**
- **프롬프트**: `06_translation_full.txt` (F_prompts)
- **KB**: `kb/translation_kb.txt` (F_files)
- **모드**: Quick (5분) / Standard (15분) / Thorough (20분+)

---

## Phase-Agent-프롬프트 매핑 요약표

| Phase | 화면 | Agent | 프롬프트 | KB |
|-------|------|-------|---------|-----|
| 0 | HomeView | - | - | - |
| 1 | Phase1View | - | - | - |
| 2 | Phase2View | Detector | 02_detector_full.txt | writer_kb.txt |
| 3 | Phase3View | Writer | 03_writer_full.txt | writer_kb.txt |
| 4 | Phase4View | Quality | 04_quality_full.txt | quality_*.txt |
| 5 | Phase5View | Title | 05_title_full.txt | title_kb.txt |
| 6 | CompletionView | - | - | - |
| Auto | AutoWriteView | Supervisor | 01_supervisor_full.txt | (전체) |
| Trans | (TBD) | Translation | 06_translation_full.txt | translation_kb.txt |

---

## 3차 분류: 기능별

### 분석 기능 (Analysis)
- 02_detector_full.txt
  - 언어 감지
  - 카테고리 분류
  - 5W1H 추출
  - 앵글 도출
  - 뉴스가치 평가

### 생성 기능 (Generation)
- 03_writer_full.txt
  - 기사 초안 생성
  - 역피라미드 구조
  - 서울경제 스타일 적용

### 교정 기능 (Correction)
- 04_quality_full.txt (PART 1: P_prompts)
  - 맞춤법 검사
  - 문법 검사
  - 띄어쓰기 교정
  - 표기법 통일

### 개선 기능 (Enhancement)
- 04_quality_full.txt (PART 2: R_prompts)
  - 문체 개선
  - 구조 최적화
  - 가독성 향상
  - C1 숏폼 / C2 롱폼

### 창작 기능 (Creative)
- 05_title_full.txt
  - TITLE-NOMICS 3.0
  - 5인 전문가 시스템
  - 창의적 제목 생성
  - 바이럴 DNA

### 번역 기능 (Translation)
- 06_translation_full.txt
  - 일본어 번역
  - 영어 번역
  - 로컬라이제이션

---

## 4차 분류: 콘텐츠 유형별

### 기업 보도자료 (Corporate) - ID 11
- 02_detector_full.txt → 기업 분석 모드
- 03_writer_full.txt → corporate 템플릿
- 적용 Agent: Detector, Writer

### 정부/공공 보도자료 (Government/Public) - ID 22
- 02_detector_full.txt → 정부/공공 분석 모드
- 03_writer_full.txt → public 템플릿
- 추가 규칙: 정치적 중립성 필수
- 적용 Agent: Detector, Writer

---

*작성일: 2025-02-18*
*버전: 1.0*
