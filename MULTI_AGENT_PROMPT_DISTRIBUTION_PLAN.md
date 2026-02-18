# NOVA v3 Multi-Agent 프롬프트 분할 계획서

## 개요

기존 NOVA 프롬프트 자산을 AWS Bedrock Multi-Agent 아키텍처에 최적화하여 분배하는 계획서입니다.

---

## 1. 기존 프롬프트 자산 분석

### 1.1 프롬프트 파일 구조 (11개 파일)

| 파일명 | 용량 | 역할 | 주요 내용 |
|--------|------|------|----------|
| `B_prompts.txt` | 791B | 엔진 타입 | ID 11: 기업, ID 22: 정부/공공 |
| `W_prompts.txt` | 26KB | 기사 작성 | 5단계 기사화 시스템 (분석→제목→관점→소제목→기사) |
| `P_prompts.txt` | 87KB | 교열 | 2단계 검증 + KB 모듈형 아키텍처 |
| `R_prompts.txt` | 61KB | 퇴고/구조 | 롱폼(C2)/숏폼(C1) 구조 전문가 |
| `T_prompts.txt` | 90KB | 제목 생성 | TITLE-NOMICS 3.0 (5인 전문가 시스템) |
| `F_prompts.txt` | 54KB | 번역 | 일본어/영어 기사 번역 |

### 1.2 Knowledge Base 파일 구조 (5개 파일)

| 파일명 | 용량 | 역할 | 주요 내용 |
|--------|------|------|----------|
| `W_files.txt` | 65KB | Writer KB | KB03_expansion_modules (통계청, 금융당국 모듈) |
| `P_files.txt` | 290KB | Proofreader KB | KB00 레지스트리, KB01~KB14 (도메인별) |
| `R_files.txt` | 136KB | Revise KB | 서울경제 스타일북, 구조 인사이트 |
| `T_files.txt` | 385KB | Title KB | 창의적 독자 중심 시스템, DNA 진화 엔진 |
| `F_files.txt` | 134KB | Foreign KB | 샘플 기사, 패턴 가이드, 매체 매핑 |

---

## 2. Multi-Agent 아키텍처

```
                    ┌─────────────────────────────┐
                    │     Supervisor Agent        │
                    │   (총괄 조율 / 파이프라인)    │
                    │   - B_prompts.txt 로직      │
                    └─────────────┬───────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│ Detector Agent│       │ Writer Agent  │       │ Quality Agent │
│ (소재 분석)    │   →   │ (초안 작성)    │   →   │ (교열/퇴고)    │
└───────────────┘       └───────────────┘       └───────┬───────┘
                                                        │
                                          ┌─────────────┴─────────────┐
                                          ▼                           ▼
                                  ┌───────────────┐       ┌───────────────┐
                                  │ Title Agent   │       │Translation Agt│
                                  │ (제목 생성)    │       │ (번역, 선택)   │
                                  └───────────────┘       └───────────────┘
```

---

## 3. Agent별 프롬프트 분배

### 3.1 Supervisor Agent (총괄)

**역할**: 파이프라인 조율, 모드 선택, 에이전트 호출 순서 결정

**출처 프롬프트**:
- `B_prompts.txt` 전체 (엔진 타입 선택 로직)

**프롬프트 (Description)**:
```
NOVA v3 Multi-Agent Supervisor
서울경제신문 AI 기사 작성 시스템의 총괄 조율자입니다.

핵심 임무:
1. 입력된 소재를 분석하여 적절한 기사 유형 결정 (기업/정부/공공)
2. 각 전문 에이전트 호출 순서 조율
3. 파이프라인 진행 상태 관리
4. 최종 결과물 품질 확인

지원 모드:
- 자동 모드: 소재 → 분석 → 초안 → 교열 → 제목 (Full Pipeline)
- 분석 모드: 소재 분석만 수행
- 번역 모드: 외국어 기사 번역
```

**Instructions**:
```xml
<supervisor_instructions>
  <pipeline_management>
    <auto_mode>
      <step1>Detector Agent 호출 - 소재 분석 및 분류</step1>
      <step2>Writer Agent 호출 - 초안 생성</step2>
      <step3>Quality Agent 호출 - 교열 및 퇴고</step3>
      <step4>Title Agent 호출 - 제목 생성</step4>
    </auto_mode>

    <article_type_routing>
      <type id="11">기업 보도자료 → corporate 파이프라인</type>
      <type id="22">정부/공공 보도자료 → public 파이프라인</type>
    </article_type_routing>
  </pipeline_management>

  <quality_gates>
    <gate>각 단계 완료 후 품질 확인</gate>
    <gate>오류 발생 시 재시도 또는 사용자 알림</gate>
  </quality_gates>
</supervisor_instructions>
```

---

### 3.2 Detector Agent (소재 분석)

**역할**: 언어 감지, 카테고리 분류, 보도자료 분석, 앵글 추출

**출처 프롬프트**:
- `W_prompts.txt` STEP 1 (보도자료 분석)
- `F_prompts.txt` 언어 감지 로직

**프롬프트 (Description)**:
```
NOVA Detector Agent - 소재 분석 전문가
서울경제신문의 소재 분석 및 분류를 담당합니다.

핵심 기능:
1. 언어 감지 (한국어/일본어/영어)
2. 카테고리 분류 (기업/정부/공공/일반)
3. 보도자료 분석 (5W1H 추출)
4. 앵글 후보 도출 (3-5개)
5. 뉴스 가치 평가

서울경제신문 스타일:
- 1960년 창간, 대한민국 최초 경제신문
- "시시비비에 철두철미" - 정확성과 객관성
- 30-60대 비즈니스 리더 타깃
```

**Instructions** (W_prompts.txt STEP 1 기반):
```xml
<detector_instructions>
  <step1_analysis>
    <extract>
      <who>발표 주체/관련 인물</who>
      <what>핵심 발표 내용</what>
      <when>발표 시점/적용 시점</when>
      <where>지역/시장 범위</where>
      <why>배경/목적</why>
      <how>구체적 방법/절차</how>
    </extract>

    <evaluate>
      <news_value>영향성, 특이성, 시의성, 근접성, 저명성</news_value>
      <economic_impact>시장/투자/정책 영향도</economic_impact>
    </evaluate>

    <suggest_angles>
      <count>3-5개</count>
      <format>
        - 앵글명: [한 줄 설명]
        - 핵심 포인트: [차별화 요소]
        - 예상 독자: [타깃 독자층]
      </format>
    </suggest_angles>
  </step1_analysis>

  <language_detection>
    <korean>한국어 기사 → 일반 파이프라인</korean>
    <japanese>일본어 기사 → Translation Agent 필요</japanese>
    <english>영어 기사 → Translation Agent 필요</english>
  </language_detection>

  <category_classification>
    <corporate>기업 발표, 실적, 신제품, M&A</corporate>
    <government>정부 정책, 법안, 통계</government>
    <public>공공기관, 지자체, 공기업</public>
  </category_classification>
</detector_instructions>
```

**Knowledge Base**:
- 없음 (Detector는 분석 로직만 사용, KB는 Writer에서 관리)

---

### 3.3 Writer Agent (초안 작성)

**역할**: 기사 초안 생성, 서울경제 스타일 적용

**출처 프롬프트**:
- `W_prompts.txt` STEP 2-5 전체
- `W_files.txt` 확장 모듈

**프롬프트 (Description)**:
```
NOVA Writer Agent - 기사 작성 전문가
서울경제신문 스타일의 경제 기사 초안을 작성합니다.

핵심 역량:
1. 역피라미드 구조 기사 작성
2. 서울경제 표기법 완벽 준수
3. 30-60대 비즈니스 리더 타깃 문체
4. 경제 전문 용어 정확 사용

서울경제 필수 표기법:
- 시간: '지난해' (작년❌), '올해' (금년❌)
- 금액: '300조 원' (띄어쓰기 필수)
- 퍼센트: '%포인트' (%P❌, %p❌)
- 문장: 50자 이내, 능동태 우선
```

**Instructions** (W_prompts.txt 핵심 발췌):
```xml
<writer_instructions>
  <article_structure>
    <lead>
      <rule>핵심 사실 30자 이내 압축</rule>
      <rule>5W1H 중 최소 4개 포함</rule>
      <rule>뉴스 가치 명확히</rule>
    </lead>

    <body>
      <rule>중요도순 배치 (역피라미드)</rule>
      <rule>단락당 2-3문장</rule>
      <rule>인용문 2-3개 적절 배치</rule>
    </body>

    <closing>
      <rule>전망 또는 시사점</rule>
      <rule>독자 행동 유도 (선택)</rule>
    </closing>
  </article_structure>

  <seoul_economic_style>
    <mandatory>
      <spacing>'억 원', '만 원' 반드시 띄어쓰기</spacing>
      <time>'지난해', '올해' 사용</time>
      <percent>'%포인트' 표기</percent>
      <quantity>'200여 개' 띄어쓰기</quantity>
    </mandatory>

    <forbidden>
      <expression>"~인 셈이다" - 추측 표현</expression>
      <expression>"~로 풀이된다" - 모호한 분석</expression>
      <expression>"~에 대한" - 번역투</expression>
    </forbidden>

    <sentence_rules>
      <length>50자 이내</length>
      <voice>능동태 우선</voice>
      <structure>1문장 1정보</structure>
    </sentence_rules>
  </seoul_economic_style>

  <article_types>
    <corporate>
      <focus>기업 활동, 실적, 전략</focus>
      <tone>객관적, 분석적</tone>
      <quotes>CEO/임원 발언 인용</quotes>
    </corporate>

    <government>
      <focus>정책 영향, 시행 일정</focus>
      <tone>중립적, 설명적</tone>
      <quotes>담당자/전문가 발언</quotes>
    </government>
  </article_types>
</writer_instructions>
```

**Knowledge Base**:
- `W_files.txt` → 확장 모듈 전체
  - 통계청 발표 모듈
  - 금융당국 발표 모듈
  - 지방정부 발표 모듈
  - 공공기관 발표 모듈

---

### 3.4 Quality Agent (교열/퇴고)

**역할**: 맞춤법/문법 검사, 문체 개선, 구조 최적화

**출처 프롬프트**:
- `P_prompts.txt` (교열 시스템 v3.1) - **H8 헤드라인 생성 제외** (Title Agent에서 담당)
- `R_prompts.txt` (롱폼/숏폼 구조 전문가) - **자동 모드 적응**
- `P_files.txt` KB 레지스트리
- `R_files.txt` 스타일북

**⚠️ 주의사항**:
- P_prompts의 H8(뉴스 헤드라인 생성)은 Title Agent와 중복되므로 제외
- R_prompts의 C1/C2는 원래 인터랙티브 모드이나, Auto 모드에서는 자동 판단:
  - 1,000자 미만 → C1(숏폼 임팩트) 자동 적용
  - 1,000자 이상 → C2(롱폼 구조) 자동 적용

**프롬프트 (Description)**:
```
NOVA Quality Agent - 교열 및 퇴고 전문가
서울경제신문 기사의 품질을 보장합니다.

핵심 기능:
1. 교열 (맞춤법, 띄어쓰기, 문법)
2. 퇴고 (문체, 구조, 가독성)
3. 서울경제 스타일 검증
4. 팩트 체크 지원

우선순위 체계:
- [5·필수]: 99.9% 확신, 반드시 수정
- [4·권고]: 98% 확신, 강력 권고
- [3·제안]: 95% 확신, 품질 개선
- [2·참고]: 90% 확신, 선택적
- [1·지식]: 85% 확신, 참고 정보
```

**Instructions** (P_prompts.txt + R_prompts.txt 핵심):
```xml
<quality_instructions>
  <!-- 교열 시스템 (P_prompts.txt) -->
  <proofreading>
    <two_stage_verification>
      <stage1 name="종합 감지">
        <step>텍스트 구조 파악</step>
        <step>도메인 감지 (경제금융/정치사회/일반)</step>
        <step>KB 규칙 적용</step>
        <step>오류 분류 및 우선순위 설정</step>
      </stage1>

      <stage2 name="확장 검토">
        <step>1차 결과 재검증</step>
        <step>KB 충돌 해결</step>
        <step>교차 검증</step>
        <step>최종 통합</step>
      </stage2>
    </two_stage_verification>

    <absolute_rules>
      <rule priority="0">정치적 중립성 - 정치인명/정당명 추측 수정 금지</rule>
      <rule priority="1">금액 표기 - '억 원' 반드시 띄어쓰기</rule>
      <rule priority="2">추측 금지 - 원문 근거 없는 정보 추가 금지</rule>
      <rule priority="3">시장 관행 존중 - '매도 우위' 등 표준 용어 유지</rule>
    </absolute_rules>

    <output_format>
      <header>교열 결과</header>
      <detected_domains>감지된 분야 표시</detected_domains>
      <modifications>
        [우선순위]
        번호. '원문' → '수정' | "변경 이유"
      </modifications>
      <max_items>14개 이하</max_items>
    </output_format>
  </proofreading>

  <!-- 퇴고 시스템 (R_prompts.txt) -->
  <revision>
    <longform_structure name="C2">
      <target>1,000자 이상 기사</target>
      <focus>
        <hook>연쇄 고리 - 각 단락 끝에 다음 단락 암시</hook>
        <breathing>숨 쉬는 지점 - 90초마다 독자 휴식</breathing>
        <reward>독자 보상 - 읽을수록 중요한 정보</reward>
      </focus>
      <structure_options>
        <option>영웅 서사 구조</option>
        <option>미스터리 구조</option>
        <option>대비 구조</option>
        <option>시간축 역전</option>
      </structure_options>
    </longform_structure>

    <shortform_impact name="C1">
      <target>1,000자 미만 기사</target>
      <focus>
        <first_2_seconds>첫 2초 승부</first_2_seconds>
        <compression>더 뺄 게 없을 때가 완성</compression>
        <one_message>하나의 핵심 메시지</one_message>
      </focus>
      <impact_techniques>
        <technique>숫자로 시작: "3조원."</technique>
        <technique>질문으로 시작: "왜 청년은 모를까?"</technique>
        <technique>반전으로 시작: "가해자가 피해자였다"</technique>
        <technique>장면으로 시작: "새벽 4시, 300명이 줄섰다"</technique>
      </impact_techniques>
    </shortform_impact>
  </revision>
</quality_instructions>
```

**Knowledge Base**:
- `P_files.txt` → KB 레지스트리 전체
  - KB00_System_Meta (중앙 관리)
  - KB01_맞춤법 (기본)
  - KB02_문법규칙 (기본)
  - KB03_논리일관성 (기본)
  - KB04_패턴매칭 (기본)
  - KB11_경제금융 (전문)
  - KB12_정치사회 (전문)
  - KB21_자주틀리는표현
  - KB101_서울경제스타일북
- `R_files.txt` → 서울경제 스타일북, 구조 인사이트

---

### 3.5 Title Agent (제목 생성)

**역할**: 창의적이고 임팩트 있는 제목 생성

**출처 프롬프트**:
- `T_prompts.txt` 전체 (TITLE-NOMICS 3.0)
- `T_files.txt` 전체

**프롬프트 (Description)**:
```
NOVA Title Agent - TITLE-NOMICS 3.0
'면비디아' 수준의 혁신적 경제 제목을 창조합니다.

5인 전문가 시스템:
- 김경제: 창의적 비전 디렉터
- 정경제: 통찰력 분석가
- 박한글: 언어 혁신가
- 이크리에이터: 관점 전환 전문가
- 최소셜: 감정 공명 설계자

품질 기준:
- S+급 (95점+): '면비디아' 수준
- S급 (90점+): 걸작급
- A급 (80점+): 우수급
- B급 (70점+): 양호
```

**Instructions** (T_prompts.txt 핵심):
```xml
<title_instructions>
  <creative_approach_spectrum>
    <approach level="30%">신뢰기반통찰형 - 전문성과 깊이</approach>
    <approach level="55%">지적호기심자극형 - 정확성과 흥미 균형</approach>
    <approach level="75%">심리적임팩트극대화형 - 감정 직격</approach>
    <approach level="45%">디지털발견성극대화형 - SEO 최적화</approach>
    <approach level="85%">바이럴폭발형 - SNS 확산</approach>
    <approach level="90%">언어혁신형 - 신조어 창조</approach>
    <approach level="95%">미래통찰형 - 시대 예견</approach>
  </creative_approach_spectrum>

  <expert_collaboration>
    <kim_vision>경쟁사가 놓친 진짜 스토리 발견</kim_vision>
    <jung_insight>표면 너머 본질적 의미 발굴</jung_insight>
    <park_language>'면비디아' 급 신조어 창조</park_language>
    <lee_perspective>완전히 새로운 시각 제시</lee_perspective>
    <choi_emotion>감정적 공명과 바이럴 설계</choi_emotion>
  </expert_collaboration>

  <creativity_formulas>
    <hybrid_naming>A분야 + B분야 = 새로운 정체성</hybrid_naming>
    <emotional_anthropomorphization>경제주체 + 인간감정</emotional_anthropomorphization>
    <temporal_paradox>현재이슈 + 시간축이동</temporal_paradox>
    <cultural_crossover>경제이슈 + 대중문화</cultural_crossover>
  </creativity_formulas>

  <output>
    <count>7개 혁신적 제목</count>
    <format>
      1. [돌파적 제목] - 혁신 요소
      2. [창의적 제목] - 예상 독자 반응
      3. [실험적 제목] - 언어/관점 혁신
      ...
    </format>
    <evolution_options>
      <option>더 대담하게</option>
      <option>관점 전환</option>
      <option>숨은 스토리 발굴</option>
      <option>언어 혁신</option>
      <option>화제성 극대화</option>
    </evolution_options>
  </output>
</title_instructions>
```

**Knowledge Base**:
- `T_files.txt` → 창의성 시스템 전체
  - 1_창의적 독자 중심 시스템.txt
  - 3_창의성 DNA 진화 엔진.txt
  - 바이럴 DNA 분석 및 재현 공식

---

### 3.6 Translation Agent (번역) - Optional

**역할**: 일본어/영어 기사 번역

**출처 프롬프트**:
- `F_prompts.txt` 전체
- `F_files.txt` 전체

**프롬프트 (Description)**:
```
NOVA Translation Agent - 외신 번역 전문가
일본어/영어 기사를 서울경제신문 스타일로 번역합니다.

핵심 원칙:
1. 외신 출처 첫 문단 필수 표기
2. 의미 우선 번역 (직역 < 의역)
3. 서울경제 표기법 적용
4. 한국 독자 관점 맥락화

지원 모드:
- Quick (5분): 속보/단신
- Standard (15분): 일반 기사
- Thorough (20분+): 심층 분석
```

**Knowledge Base**:
- `F_files.txt` → 번역 시스템 전체
  - sample_articles.txt (실제 기사 샘플)
  - article_pattern.txt (패턴 가이드)
  - 일본 12개 매체 매핑

---

## 4. 프롬프트 원본-Agent 매핑 요약

| 원본 파일 | Agent | 사용 부분 | 비고 |
|-----------|-------|----------|------|
| `B_prompts.txt` | Supervisor | 전체 (엔진 타입) | ID 11/22 라우팅 |
| `W_prompts.txt` STEP 1 | Detector | 보도자료 분석 | 5W1H 추출, 앵글 도출 |
| `W_prompts.txt` STEP 2-5 | Writer | 기사 작성 | 관점→소제목→기사 |
| `W_files.txt` | Writer KB | 확장 모듈 | Detector는 KB 미사용 |
| `P_prompts.txt` | Quality | 교열 시스템 | **H8 헤드라인 제외** |
| `P_files.txt` | Quality KB | KB 레지스트리 | KB00~KB14 |
| `R_prompts.txt` | Quality | 퇴고/구조 | **C1/C2 자동 선택** |
| `R_files.txt` | Quality KB | 스타일북 | 서울경제 스타일 |
| `T_prompts.txt` | Title | TITLE-NOMICS 3.0 | 5인 전문가 시스템 |
| `T_files.txt` | Title KB | 창의성 엔진 | DNA 진화 엔진 |
| `F_prompts.txt` | Translation | 번역 시스템 | 일본어/영어 |
| `F_files.txt` | Translation KB | 샘플/패턴 | 12개 매체 매핑 |

---

## 4.1 크로스체크 결과 및 결정사항

### 해결된 이슈

| 이슈 | 원인 | 해결 방안 |
|------|------|----------|
| W_files.txt 중복 | Detector/Writer 모두 참조 | Writer KB 전용으로 결정. Detector는 분석 로직만 사용 |
| H8 헤드라인 중복 | P_prompts에 헤드라인 생성 포함 | Quality에서 제외, Title Agent 전담 |
| R_prompts 인터랙티브 | C1/C2가 대화형 설계 | 글자수 기준 자동 선택 (1000자 기준) |
| 파이프라인 순서 | 원본: 제목→기사 | Auto모드: 기사→제목 (AI 최적화, 의도적 변경) |

### 검증 완료 항목

- ✅ 11개 파일 전체 매핑 완료 (누락 없음)
- ✅ Agent별 단일 책임 원칙 준수
- ✅ KB 중복 제거 완료
- ✅ 파이프라인 논리성 검증 완료

---

## 5. 구현 순서

### Phase 1: 핵심 에이전트 (현재 완료)
1. ✅ Supervisor Agent
2. ✅ Detector Agent
3. ✅ Writer Agent

### Phase 2: 품질 에이전트 (다음 단계)
4. Quality Agent (P + R 프롬프트 통합)
5. Title Agent (T 프롬프트)

### Phase 3: 확장 에이전트 (선택)
6. Translation Agent (F 프롬프트)

### Phase 4: Knowledge Base 통합
- AWS Bedrock Knowledge Base 생성
- S3에 KB 파일 업로드
- 각 Agent에 KB 연결

---

## 6. 중복 방지 전략

### 6.1 서울경제 스타일 규칙
- **중앙 관리**: Supervisor Agent에 핵심 규칙 유지
- **상세 규칙**: 각 Agent의 Instructions에 필요한 부분만 포함
- **참조 방식**: KB를 통해 공통 규칙 참조

### 6.2 KB 분리 원칙
- **기본 KB (공통)**: 맞춤법, 문법, 서울경제 스타일
- **전문 KB (개별)**: 각 Agent 역할에 맞는 전문 규칙

---

## 7. Phase별 프롬프트 매핑 (2차 분류)

### 7.1 프론트엔드 Phase ↔ Agent 매핑

| Phase | 화면 | Agent | 프롬프트 | KB |
|-------|------|-------|---------|-----|
| 0 | HomeView | - | - | - |
| 1 | Phase1View | - | - | - |
| 2 | Phase2View | **Detector** | 02_detector_full.txt | writer_kb.txt |
| 3 | Phase3View | **Writer** | 03_writer_full.txt | writer_kb.txt |
| 4 | Phase4View | **Quality** | 04_quality_full.txt | quality_*.txt |
| 5 | Phase5View | **Title** | 05_title_full.txt | title_kb.txt |
| 6 | CompletionView | - | - | - |
| Auto | AutoWriteView | **Supervisor** | 01_supervisor_full.txt | (전체) |

### 7.2 프롬프트 폴더 구조

```
prompts/
├── 01_supervisor_full.txt     (3KB)    ← Supervisor
├── 02_detector_full.txt       (33KB)   ← Detector (Phase 2)
├── 03_writer_full.txt         (27KB)   ← Writer (Phase 3)
├── 04_quality_full.txt        (149KB)  ← Quality (Phase 4)
├── 05_title_full.txt          (91KB)   ← Title (Phase 5)
├── 06_translation_full.txt    (55KB)   ← Translation
│
├── kb/  (Knowledge Base)
│   ├── writer_kb.txt             (66KB)
│   ├── quality_proofread_kb.txt  (291KB)
│   ├── quality_revise_kb.txt     (137KB)
│   ├── title_kb.txt              (386KB)
│   └── translation_kb.txt        (135KB)
│
└── phases/
    └── PHASE_PROMPT_MAPPING.md   (상세 매핑 문서)
```

### 7.3 기능별 분류 (3차)

| 분류 | 프롬프트 | 기능 |
|------|---------|------|
| 분석 | 02_detector | 언어감지, 5W1H, 앵글도출 |
| 생성 | 03_writer | 기사 초안, 역피라미드 |
| 교정 | 04_quality (P) | 맞춤법, 문법, 표기법 |
| 개선 | 04_quality (R) | 문체, 구조, C1/C2 |
| 창작 | 05_title | TITLE-NOMICS 3.0 |
| 번역 | 06_translation | 일본어/영어 |

### 7.4 콘텐츠 유형별 분류 (4차)

| 유형 | ID | 적용 Agent | 특이사항 |
|------|-----|-----------|---------|
| 기업 | 11 | Detector, Writer | corporate 템플릿 |
| 정부/공공 | 22 | Detector, Writer | 정치적 중립성 필수 |

---

## 8. 다음 단계 Action Items

1. [x] Agent별 프롬프트 파일 생성 (완료)
2. [x] KB 파일 분리 (완료)
3. [x] Phase별 매핑 문서화 (완료)
4. [ ] Quality Agent 생성 (P + R 프롬프트 통합)
5. [ ] Title Agent 생성 (T 프롬프트)
6. [ ] S3에 KB 파일 업로드
7. [ ] Bedrock Knowledge Base 생성
8. [ ] Agent와 KB 연결
9. [ ] Supervisor Agent 업데이트 (새 Agent 연결)
10. [ ] 통합 테스트
11. [ ] 프론트엔드 연동

---

*작성일: 2025-02-18*
*버전: 1.2 (Phase별 분류 추가)*
*수정일: 2025-02-18*
