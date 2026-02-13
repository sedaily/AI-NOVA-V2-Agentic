#!/bin/bash

# p2-two 서비스 로그 그룹 생성

aws logs create-log-group --log-group-name /aws/lambda/p2-two-prompt --region us-east-1
aws logs create-log-group --log-group-name /aws/lambda/p2-two-conversation --region us-east-1
aws logs create-log-group --log-group-name /aws/lambda/p2-two-usage --region us-east-1

echo "로그 그룹 생성 완료"