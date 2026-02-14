#!/bin/bash

BUCKET_NAME="nexus-title-hub-frontend"
OAI_ID="E3SN3SSHH62CS4"

echo "🔒 S3 버킷 정책 업데이트 중..."

# 버킷 정책 JSON 생성
cat > bucket-policy.json <<EOF
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

# 버킷 정책 적용
aws s3api put-bucket-policy \
    --bucket "$BUCKET_NAME" \
    --policy file://bucket-policy.json

if [ $? -eq 0 ]; then
    echo "✅ S3 버킷 정책 업데이트 완료"
else
    echo "⚠️ 버킷 정책 업데이트 실패. 퍼블릭 액세스 차단 설정을 확인하세요."
    echo ""
    echo "AWS 콘솔에서 다음 설정을 확인하세요:"
    echo "1. S3 버킷 → 권한 탭 → 퍼블릭 액세스 차단"
    echo "2. '버킷 정책을 통해 부여된 퍼블릭 액세스 차단' 해제"
fi

# 임시 파일 삭제
rm -f bucket-policy.json

echo ""
echo "🌐 웹사이트 접속 URL:"
echo "https://d1s58eamawxu4.cloudfront.net"
echo ""
echo "⏱️ CloudFront 배포가 완전히 활성화되기까지 15-20분 정도 걸립니다."