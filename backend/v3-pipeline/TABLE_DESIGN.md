# NOVA v3 Pipeline - DynamoDB Table Design

## Table: nova-v3-pipeline

### Primary Key
- **Partition Key**: `pipelineId` (String)

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| pipelineId | String | Unique ID for pipeline session (UUID) |
| userId | String | User identifier |
| currentPhase | Number | Current phase (1-6, 6=completed) |
| sourceText | String | Original source material |
| sourceType | String | Type: press_release, interview, memo |
| analysisResult | Map | Phase 1 result (angles, summary) |
| selectedAngle | Map | User-selected angle from Phase 2 |
| draft | String | Generated draft from Phase 3 |
| proofreadResult | Map | Phase 4-1 result (corrected, corrections) |
| revisedResult | Map | Phase 4-2 result (revised, revisions) |
| titleSuggestions | List | Phase 5 title suggestions |
| selectedTitle | String | Final selected title |
| finalArticle | String | Complete article (title + body) |
| createdAt | String | ISO timestamp |
| updatedAt | String | ISO timestamp |

### GSI: userId-index
- **Partition Key**: `userId`
- **Sort Key**: `createdAt`
- **Purpose**: Query user's pipeline history

### Data Flow

```
Phase 1 (소재)
├── Input: sourceText, sourceType
└── Output: analysisResult { angles[], summary, newsValue }

Phase 2 (구성)
├── Input: User selects from angles
└── Output: selectedAngle { id, title, description, keywords }

Phase 3 (초안)
├── Input: sourceText + selectedAngle
└── Output: draft (string), wordCount

Phase 4 (교열/퇴고)
├── Input: draft
├── Proofread Output: proofreadResult { corrected, corrections[] }
└── Revise Output: revisedResult { revised, revisions[], readabilityScore }

Phase 5 (제목)
├── Input: revisedResult.revised (or draft)
└── Output: titleSuggestions[], selectedTitle

Phase 6 (완료)
└── Output: finalArticle = selectedTitle + revised
```

### Sample Item

```json
{
  "pipelineId": "550e8400-e29b-41d4-a716-446655440000",
  "userId": "user123",
  "currentPhase": 3,
  "sourceText": "삼성전자가 AI 반도체 시장 공략을 위해...",
  "sourceType": "press_release",
  "analysisResult": {
    "angles": [
      {
        "id": 1,
        "title": "경제적 파급효과",
        "description": "투자 규모와 시장 영향 중심",
        "recommended": true,
        "keywords": ["투자", "시장", "성장"]
      }
    ],
    "summary": "삼성전자 AI 반도체 1조원 투자 발표",
    "newsValue": "high"
  },
  "selectedAngle": {
    "id": 1,
    "title": "경제적 파급효과"
  },
  "draft": "삼성전자가 인공지능(AI) 반도체 시장 선점을 위해...",
  "proofreadResult": null,
  "revisedResult": null,
  "titleSuggestions": null,
  "selectedTitle": null,
  "finalArticle": null,
  "createdAt": "2025-02-18T14:30:00Z",
  "updatedAt": "2025-02-18T14:35:00Z"
}
```

### Create Table Command

```bash
aws dynamodb create-table \
  --table-name nova-v3-pipeline \
  --attribute-definitions \
    AttributeName=pipelineId,AttributeType=S \
    AttributeName=userId,AttributeType=S \
    AttributeName=createdAt,AttributeType=S \
  --key-schema \
    AttributeName=pipelineId,KeyType=HASH \
  --global-secondary-indexes \
    "[{\"IndexName\":\"userId-index\",\"KeySchema\":[{\"AttributeName\":\"userId\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"createdAt\",\"KeyType\":\"RANGE\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}}]" \
  --billing-mode PAY_PER_REQUEST \
  --region ap-northeast-2
```
