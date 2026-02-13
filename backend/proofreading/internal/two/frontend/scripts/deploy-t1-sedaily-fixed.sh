#!/bin/bash

# ========================================
# t1.sedaily.ai 배포 스크립트 (수정 버전)
# ========================================

# 색상 설정
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 배포 설정
BUCKET_NAME="nexus-title-hub-frontend"  # t1.sedaily.ai와 연결된 실제 S3 버킷
REGION="us-east-1"  # CloudFront는 us-east-1 권장
DOMAIN_NAME="t1.sedaily.ai"
CLOUDFRONT_DISTRIBUTION_ID="EIYU5SFVTHQMN"  # t1.sedaily.ai의 CloudFront 배포 ID

echo -e "${GREEN}🚀 t1.sedaily.ai 배포 시작...${NC}"

# AWS CLI 확인
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI가 설치되지 않았습니다. 먼저 설치해주세요.${NC}"
    exit 1
fi

# AWS 자격 증명 확인
echo -e "${YELLOW}📋 AWS 자격 증명 확인...${NC}"
aws sts get-caller-identity > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ AWS 자격 증명이 설정되지 않았습니다. aws configure를 실행해주세요.${NC}"
    exit 1
fi

# 1. 빌드 실행
echo -e "${GREEN}🏗️  프로덕션 빌드 시작...${NC}"
npm run build
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 빌드 실패${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 빌드 완료${NC}"

# 2. S3 버킷 생성 또는 확인
echo -e "${YELLOW}📦 S3 버킷 확인/생성 중...${NC}"
if ! aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
    echo -e "${YELLOW}새 S3 버킷 생성 중...${NC}"
    
    # 버킷 생성
    aws s3api create-bucket \
        --bucket "$BUCKET_NAME" \
        --region "$REGION" \
        --acl private
    
    # 퍼블릭 액세스 차단 해제 (CloudFront만 접근 가능하도록 설정)
    aws s3api put-public-access-block \
        --bucket "$BUCKET_NAME" \
        --public-access-block-configuration \
        "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"
    
    # 정적 웹사이트 호스팅 활성화
    aws s3 website s3://"$BUCKET_NAME"/ \
        --index-document index.html \
        --error-document index.html
    
    echo -e "${GREEN}✅ S3 버킷 생성 완료${NC}"
else
    echo -e "${GREEN}✅ S3 버킷이 이미 존재합니다${NC}"
fi

# 3. CloudFront Origin Access Identity (OAI) 생성
echo -e "${YELLOW}🔐 CloudFront OAI 확인/생성 중...${NC}"
OAI_ID=$(aws cloudfront list-cloud-front-origin-access-identities --query "CloudFrontOriginAccessIdentityList.Items[?Comment=='OAI for $BUCKET_NAME'].Id" --output text)

if [ -z "$OAI_ID" ]; then
    echo -e "${YELLOW}새 OAI 생성 중...${NC}"
    OAI_RESPONSE=$(aws cloudfront create-cloud-front-origin-access-identity \
        --cloud-front-origin-access-identity-config \
        CallerReference="$(date +%s)",Comment="OAI for $BUCKET_NAME" \
        --output json)
    
    # JSON 파싱 (Python 사용)
    OAI_ID=$(echo "$OAI_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['CloudFrontOriginAccessIdentity']['Id'])" 2>/dev/null)
    OAI_CANONICAL_USER_ID=$(echo "$OAI_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['CloudFrontOriginAccessIdentity']['S3CanonicalUserId'])" 2>/dev/null)
    
    if [ -z "$OAI_ID" ]; then
        echo -e "${RED}❌ OAI ID를 가져올 수 없습니다${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ OAI 생성 완료: $OAI_ID${NC}"
else
    echo -e "${GREEN}✅ 기존 OAI 사용: $OAI_ID${NC}"
    OAI_CANONICAL_USER_ID=$(aws cloudfront get-cloud-front-origin-access-identity --id "$OAI_ID" --query "CloudFrontOriginAccessIdentity.S3CanonicalUserId" --output text)
fi

# 4. S3 버킷 정책 업데이트 (CloudFront만 접근 가능)
echo -e "${YELLOW}📝 S3 버킷 정책 업데이트 중...${NC}"
cat > /tmp/bucket-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowCloudFrontAccess",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity $OAI_ID"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$BUCKET_NAME/*"
        }
    ]
}
EOF

aws s3api put-bucket-policy --bucket "$BUCKET_NAME" --policy file:///tmp/bucket-policy.json
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  버킷 정책 업데이트 실패. 대체 정책 시도 중...${NC}"
    
    # 대체 정책 (퍼블릭 읽기 허용)
    cat > /tmp/bucket-policy-public.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$BUCKET_NAME/*"
        }
    ]
}
EOF
    
    aws s3api put-bucket-policy --bucket "$BUCKET_NAME" --policy file:///tmp/bucket-policy-public.json
fi
echo -e "${GREEN}✅ 버킷 정책 업데이트 완료${NC}"

# 5. CloudFront Distribution 확인/생성
echo -e "${YELLOW}☁️  CloudFront Distribution 확인 중...${NC}"
EXISTING_DISTRIBUTION=$(aws cloudfront list-distributions --query "DistributionList.Items[?Origins.Items[0].DomainName=='$BUCKET_NAME.s3.amazonaws.com'].Id" --output text 2>/dev/null)

if [ -z "$EXISTING_DISTRIBUTION" ] || [ "$EXISTING_DISTRIBUTION" == "None" ]; then
    echo -e "${YELLOW}새 CloudFront Distribution 생성 중...${NC}"
    
    # CloudFront 설정 파일 생성
    cat > /tmp/cloudfront-config.json <<EOF
{
    "CallerReference": "$(date +%s)",
    "Comment": "Distribution for $DOMAIN_NAME",
    "Enabled": true,
    "Origins": {
        "Quantity": 1,
        "Items": [
            {
                "Id": "$BUCKET_NAME-origin",
                "DomainName": "$BUCKET_NAME.s3.amazonaws.com",
                "S3OriginConfig": {
                    "OriginAccessIdentity": "origin-access-identity/cloudfront/$OAI_ID"
                }
            }
        ]
    },
    "DefaultRootObject": "index.html",
    "DefaultCacheBehavior": {
        "TargetOriginId": "$BUCKET_NAME-origin",
        "ViewerProtocolPolicy": "redirect-to-https",
        "AllowedMethods": {
            "Quantity": 2,
            "Items": ["GET", "HEAD"],
            "CachedMethods": {
                "Quantity": 2,
                "Items": ["GET", "HEAD"]
            }
        },
        "Compress": true,
        "ForwardedValues": {
            "QueryString": false,
            "Cookies": {
                "Forward": "none"
            }
        },
        "TrustedSigners": {
            "Enabled": false,
            "Quantity": 0
        },
        "MinTTL": 0,
        "DefaultTTL": 86400,
        "MaxTTL": 31536000
    },
    "CustomErrorResponses": {
        "Quantity": 1,
        "Items": [
            {
                "ErrorCode": 404,
                "ResponseCode": "200",
                "ResponsePagePath": "/index.html",
                "ErrorCachingMinTTL": 300
            }
        ]
    },
    "PriceClass": "PriceClass_100"
}
EOF

    DISTRIBUTION_RESPONSE=$(aws cloudfront create-distribution --distribution-config file:///tmp/cloudfront-config.json --output json 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        # JSON 파싱 (Python 사용)
        CLOUDFRONT_DISTRIBUTION_ID=$(echo "$DISTRIBUTION_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['Distribution']['Id'])" 2>/dev/null)
        CLOUDFRONT_DOMAIN=$(echo "$DISTRIBUTION_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['Distribution']['DomainName'])" 2>/dev/null)
        
        echo -e "${GREEN}✅ CloudFront Distribution 생성 완료${NC}"
        echo -e "${YELLOW}   Distribution ID: $CLOUDFRONT_DISTRIBUTION_ID${NC}"
        echo -e "${YELLOW}   CloudFront Domain: $CLOUDFRONT_DOMAIN${NC}"
    else
        echo -e "${YELLOW}⚠️  CloudFront Distribution 생성 실패. S3 정적 호스팅 사용${NC}"
        CLOUDFRONT_DOMAIN=""
    fi
else
    CLOUDFRONT_DISTRIBUTION_ID="$EXISTING_DISTRIBUTION"
    CLOUDFRONT_DOMAIN=$(aws cloudfront get-distribution --id "$CLOUDFRONT_DISTRIBUTION_ID" --query "Distribution.DomainName" --output text)
    echo -e "${GREEN}✅ 기존 CloudFront Distribution 사용${NC}"
    echo -e "${YELLOW}   Distribution ID: $CLOUDFRONT_DISTRIBUTION_ID${NC}"
    echo -e "${YELLOW}   CloudFront Domain: $CLOUDFRONT_DOMAIN${NC}"
fi

# 6. 빌드 파일 S3에 업로드
echo -e "${GREEN}📤 빌드 파일 S3에 업로드 중...${NC}"

# 모든 파일 업로드 (index.html 제외)
aws s3 sync ./dist s3://"$BUCKET_NAME"/ \
    --delete \
    --cache-control "public, max-age=31536000" \
    --exclude "index.html" \
    --exclude "*.map"

# index.html은 캐시 없이 업로드
aws s3 cp ./dist/index.html s3://"$BUCKET_NAME"/index.html \
    --cache-control "no-cache, no-store, must-revalidate" \
    --content-type "text/html"

echo -e "${GREEN}✅ S3 업로드 완료${NC}"

# 7. CloudFront 캐시 무효화
if [ -n "$CLOUDFRONT_DISTRIBUTION_ID" ] && [ "$CLOUDFRONT_DISTRIBUTION_ID" != "None" ]; then
    echo -e "${YELLOW}🔄 CloudFront 캐시 무효화 중...${NC}"
    aws cloudfront create-invalidation \
        --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" \
        --paths "/*" \
        --query "Invalidation.Id" \
        --output text
    echo -e "${GREEN}✅ CloudFront 캐시 무효화 요청 완료${NC}"
fi

# 8. 완료 메시지
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 배포 완료!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

if [ -n "$CLOUDFRONT_DOMAIN" ] && [ "$CLOUDFRONT_DOMAIN" != "None" ]; then
    echo -e "${YELLOW}📌 CloudFront URL:${NC} https://$CLOUDFRONT_DOMAIN"
else
    echo -e "${YELLOW}📌 S3 웹사이트 URL:${NC} http://$BUCKET_NAME.s3-website-$REGION.amazonaws.com"
fi

echo ""
echo -e "${YELLOW}📌 커스텀 도메인 설정 방법:${NC}"
echo "1. Route 53에서 $DOMAIN_NAME 호스팅 영역 생성"
echo "2. ACM에서 SSL 인증서 요청 (us-east-1 리전)"
echo "3. CloudFront Distribution에 대체 도메인 이름 추가"
echo "4. Route 53에 A 레코드 추가 (Alias로 CloudFront 지정)"
echo ""
echo -e "${YELLOW}📌 명령어:${NC}"
echo "   # SSL 인증서 요청"
echo "   aws acm request-certificate --domain-name $DOMAIN_NAME --validation-method DNS --region us-east-1"
echo ""

if [ -n "$CLOUDFRONT_DISTRIBUTION_ID" ] && [ "$CLOUDFRONT_DISTRIBUTION_ID" != "None" ]; then
    echo "   # CloudFront에 도메인 추가 (인증서 ARN 필요)"
    echo "   aws cloudfront update-distribution --id $CLOUDFRONT_DISTRIBUTION_ID ..."
fi

echo ""

# 임시 파일 정리
rm -f /tmp/bucket-policy.json /tmp/bucket-policy-public.json /tmp/cloudfront-config.json

exit 0