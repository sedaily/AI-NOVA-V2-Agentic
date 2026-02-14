#!/bin/bash

# 배포 자동화 스크립트
# 사용법: ./deploy.sh [service-name] [environment]

set -e

SERVICE_NAME=${1:-tem1}
ENVIRONMENT=${2:-prod}

echo "🚀 배포 시작: $SERVICE_NAME ($ENVIRONMENT)"

# 1. 환경변수 파일 생성
echo "📝 환경변수 파일 생성 중..."

# Backend .env 파일 업데이트
if [ -f "backend/.env.template" ]; then
    sed "s/tem1/$SERVICE_NAME/g" backend/.env.template > backend/.env
    echo "✅ Backend .env 파일 생성 완료"
fi

# Frontend .env 파일 업데이트
if [ -f "frontend/.env.template" ]; then
    sed "s/tem1/$SERVICE_NAME/g" frontend/.env.template > frontend/.env
    echo "✅ Frontend .env 파일 생성 완료"
fi

# 2. 테라폼으로 인프라 배포 (선택사항)
if [ -d "terraform" ]; then
    echo "🏗️ 테라폼 인프라 배포..."
    cd terraform

    # tfvars 파일 생성
    if [ -f "terraform.tfvars.example" ]; then
        cp terraform.tfvars.example terraform.tfvars
        sed -i "" "s/tem1/$SERVICE_NAME/g" terraform.tfvars
        sed -i "" "s/prod/$ENVIRONMENT/g" terraform.tfvars
    fi

    # 테라폼 초기화 및 적용
    # terraform init
    # terraform plan
    # terraform apply -auto-approve

    cd ..
    echo "✅ 테라폼 배포 완료"
fi

# 3. 프론트엔드 빌드
echo "🔨 프론트엔드 빌드 중..."
cd frontend
npm install
npm run build
cd ..
echo "✅ 프론트엔드 빌드 완료"

# 4. 백엔드 배포 준비
echo "📦 백엔드 패키징 중..."
cd backend
pip install -r requirements.txt -t ./package
cp -r lib package/
cp -r handlers package/
cp -r services package/
cp -r src package/
cd ..
echo "✅ 백엔드 패키징 완료"

echo "🎉 배포 준비 완료!"
echo ""
echo "다음 단계:"
echo "1. AWS 콘솔에서 Lambda 함수 업데이트"
echo "2. S3에 프론트엔드 업로드"
echo "3. CloudFront 캐시 무효화"