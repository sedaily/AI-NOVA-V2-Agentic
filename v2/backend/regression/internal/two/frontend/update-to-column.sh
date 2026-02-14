#!/bin/bash

# Column Service Update Script
# T5 -> C1, C7 -> C2로 변경하고 제목 관련 텍스트를 칼럼으로 변경

echo "🔄 Updating frontend to Column Service..."

# Find all JS/JSX files and update
find src -type f \( -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" \) -exec sed -i '' \
    -e "s/'T5'/'C1'/g" \
    -e 's/"T5"/"C1"/g' \
    -e "s/'C7'/'C2'/g" \
    -e 's/"C7"/"C2"/g' \
    -e 's/T5 Chat/C1 칼럼/g' \
    -e 's/C7 Chat/C2 칼럼/g' \
    -e 's/T5:/C1:/g' \
    -e 's/C7:/C2:/g' \
    -e 's/T10/C1/g' \
    -e 's/핵심을 꿰뚫는 타이틀/전문적인 칼럼 작성/g' \
    -e 's/상상 그 이상의 창의적 제목/독창적인 관점의 칼럼/g' \
    -e 's/제목 생성/칼럼 작성/g' \
    -e 's/제목을 생성/칼럼을 작성/g' \
    -e 's/타이틀 생성/칼럼 작성/g' \
    -e 's/기본 제목 생성/기본 칼럼 작성/g' \
    -e 's/고급 제목 생성/고급 칼럼 작성/g' \
    -e 's/제목 생성 무제한/칼럼 작성 무제한/g' \
    -e 's/T5 엔진/칼럼 기본 엔진/g' \
    -e 's/C7 엔진/칼럼 고급 엔진/g' \
    -e 's/T5, C7 엔진/C1, C2 엔진/g' \
    {} +

# Update specific service descriptions
find src -type f \( -name "*.js" -o -name "*.jsx" \) -exec sed -i '' \
    -e 's/빠르고 정확한 제목 생성에 최적화/전문적이고 균형잡힌 칼럼 작성에 최적화/g' \
    -e 's/더 창의적이고 자연스러운 제목을 생성/독창적인 시각과 날카로운 분석을 제공/g' \
    -e 's/빠른 제목 생성에 최적화/빠른 칼럼 작성에 최적화/g' \
    -e 's/5가지 유형의 제목을/다양한 관점의 칼럼을/g' \
    -e 's/5가지 스타일로 제목을 생성/다양한 스타일로 칼럼을 작성/g' \
    {} +

echo "✅ File updates completed!"

# Copy new env file if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.column" ]; then
        cp .env.column .env
        echo "✅ Environment file copied from .env.column to .env"
    fi
fi

echo "🎉 Column Service update completed!"
echo ""
echo "Next steps:"
echo "1. Review the changes"
echo "2. Run: npm install"
echo "3. Run: npm run dev"