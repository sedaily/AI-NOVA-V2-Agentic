#!/bin/bash

# 기존 테이블 삭제 (있는 경우)
echo "기존 테이블 삭제 중..."
aws dynamodb delete-table --table-name nx-tt-dev-ver3-prompts --region us-east-1 2>/dev/null || true
sleep 5

# 1. Prompts 테이블 생성 (설명과 지침 저장)
echo "Prompts 테이블 생성 중..."
aws dynamodb create-table \
    --table-name nx-tt-dev-ver3-prompts \
    --attribute-definitions \
        AttributeName=id,AttributeType=S \
    --key-schema \
        AttributeName=id,KeyType=HASH \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region us-east-1

echo "Prompts 테이블 생성 완료"

# 2. Files 테이블 생성 (파일들 저장)
echo "Files 테이블 생성 중..."
aws dynamodb create-table \
    --table-name nx-tt-dev-ver3-files \
    --attribute-definitions \
        AttributeName=promptId,AttributeType=S \
        AttributeName=fileId,AttributeType=S \
    --key-schema \
        AttributeName=promptId,KeyType=HASH \
        AttributeName=fileId,KeyType=RANGE \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region us-east-1

echo "Files 테이블 생성 완료"

# 테이블이 생성될 때까지 대기
echo "테이블 생성 확인 중..."
aws dynamodb wait table-exists --table-name nx-tt-dev-ver3-prompts --region us-east-1
aws dynamodb wait table-exists --table-name nx-tt-dev-ver3-files --region us-east-1

# 초기 데이터 삽입 - T5 프롬프트
echo "T5 초기 데이터 삽입 중..."
aws dynamodb put-item \
    --table-name nx-tt-dev-ver3-prompts \
    --item '{
        "id": {"S": "T5"},
        "description": {"S": "T5 엔진은 빠른 제목 생성에 최적화되어 있습니다. 5가지 유형의 제목을 8초 이내에 생성합니다."},
        "instruction": {"S": "다음 기사를 읽고 저널리즘 충실형, 균형잡힌 후킹형, 클릭유도형, SEO 최적화형, 소셜미디어형 5가지 스타일로 제목을 생성하세요."},
        "updatedAt": {"S": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"}
    }' \
    --region us-east-1

# 초기 데이터 삽입 - H8 프롬프트
echo "H8 초기 데이터 삽입 중..."
aws dynamodb put-item \
    --table-name nx-tt-dev-ver3-prompts \
    --item '{
        "id": {"S": "H8"},
        "description": {"S": "H8 엔진은 정교한 제목 생성에 최적화되어 있습니다. 8가지 유형의 제목을 15초 이내에 생성합니다."},
        "instruction": {"S": "다음 기사를 분석하여 간단명료형, 5W1H형, 수식어활용형, 스토리텔링형, 고정값활용형, 위트한스푼형, 부드러운문장형, 대비되는상황형 8가지 스타일로 제목을 생성하세요."},
        "updatedAt": {"S": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"}
    }' \
    --region us-east-1

# T5용 샘플 파일 추가
echo "T5 샘플 파일 추가 중..."
aws dynamodb put-item \
    --table-name nx-tt-dev-ver3-files \
    --item '{
        "promptId": {"S": "T5"},
        "fileId": {"S": "'$(uuidgen)'"},
        "fileName": {"S": "t5_context.txt"},
        "fileContent": {"S": "T5 엔진 컨텍스트: 신속성과 정확성을 중시하며, 독자의 관심을 끄는 제목을 생성합니다."},
        "createdAt": {"S": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"}
    }' \
    --region us-east-1

# H8용 샘플 파일 추가
echo "H8 샘플 파일 추가 중..."
aws dynamodb put-item \
    --table-name nx-tt-dev-ver3-files \
    --item '{
        "promptId": {"S": "H8"},
        "fileId": {"S": "'$(uuidgen)'"},
        "fileName": {"S": "h8_context.txt"},
        "fileContent": {"S": "H8 엔진 컨텍스트: 창의성과 다양성을 중시하며, 여러 관점에서 제목을 생성합니다."},
        "createdAt": {"S": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"}
    }' \
    --region us-east-1

echo "모든 테이블 설정 완료!"
echo ""
echo "생성된 테이블:"
echo "1. nx-tt-dev-ver3-prompts (설명, 지침)"
echo "2. nx-tt-dev-ver3-files (파일들)"