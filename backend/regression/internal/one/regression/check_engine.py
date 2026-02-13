import boto3
import json

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('sedaily-column-prompts')

# 11 엔진 조회
response = table.get_item(Key={'promptId': '11'})

if 'Item' in response:
    item = response['Item']
    print("=== 엔진 11 (internal/one) ===")
    print(f"description: {item.get('description', '')[:200]}")
    print(f"\ninstruction: {item.get('instruction', '')[:200]}")
else:
    print("11 엔진을 찾을 수 없습니다.")

print("\n" + "="*50 + "\n")

# 22 엔진 조회
response2 = table.get_item(Key={'promptId': '22'})

if 'Item' in response2:
    item2 = response2['Item']
    print("=== 엔진 22 (internal/one) ===")
    print(f"description: {item2.get('description', '')[:200]}")
    print(f"\ninstruction: {item2.get('instruction', '')[:200]}")
else:
    print("22 엔진을 찾을 수 없습니다.")
