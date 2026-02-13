#!/bin/bash

# JWT Authorizer Test Script
# This script creates a test user in Cognito and retrieves JWT tokens for testing

set -e

# Configuration
USER_POOL_ID="us-east-1_ohLOswurY"
CLIENT_ID=""
EMAIL="test-multitenant@example.com"
PASSWORD="TestPassword123!"
REGION="us-east-1"

echo "=== JWT Authorizer Test Script ==="
echo "User Pool ID: $USER_POOL_ID"
echo "Test Email: $EMAIL"
echo ""

# Step 1: Get the Cognito User Pool Client ID
echo "Step 1: Getting Cognito User Pool Client ID..."
CLIENT_ID=$(aws cognito-idp list-user-pool-clients \
    --user-pool-id $USER_POOL_ID \
    --region $REGION \
    --query 'UserPoolClients[0].ClientId' \
    --output text)

if [ "$CLIENT_ID" = "None" ] || [ -z "$CLIENT_ID" ]; then
    echo "Error: Could not find User Pool Client ID"
    exit 1
fi

echo "Client ID: $CLIENT_ID"
echo ""

# Step 2: Create test user (if not exists)
echo "Step 2: Creating test user..."
if aws cognito-idp admin-get-user \
    --user-pool-id $USER_POOL_ID \
    --username $EMAIL \
    --region $REGION >/dev/null 2>&1; then
    echo "User already exists: $EMAIL"
else
    echo "Creating new user: $EMAIL"
    aws cognito-idp admin-create-user \
        --user-pool-id $USER_POOL_ID \
        --username $EMAIL \
        --user-attributes Name=email,Value=$EMAIL Name=email_verified,Value=true \
        --temporary-password "TempPass123!" \
        --message-action SUPPRESS \
        --region $REGION

    echo "Setting permanent password..."
    aws cognito-idp admin-set-user-password \
        --user-pool-id $USER_POOL_ID \
        --username $EMAIL \
        --password $PASSWORD \
        --permanent \
        --region $REGION

    echo "User created successfully!"
fi
echo ""

# Step 3: Authenticate and get JWT tokens
echo "Step 3: Authenticating user and getting JWT tokens..."
AUTH_RESPONSE=$(aws cognito-idp admin-initiate-auth \
    --user-pool-id $USER_POOL_ID \
    --client-id $CLIENT_ID \
    --auth-flow ADMIN_NO_SRP_AUTH \
    --auth-parameters USERNAME=$EMAIL,PASSWORD=$PASSWORD \
    --region $REGION)

# Extract tokens
ACCESS_TOKEN=$(echo $AUTH_RESPONSE | jq -r '.AuthenticationResult.AccessToken')
ID_TOKEN=$(echo $AUTH_RESPONSE | jq -r '.AuthenticationResult.IdToken')
REFRESH_TOKEN=$(echo $AUTH_RESPONSE | jq -r '.AuthenticationResult.RefreshToken')

if [ "$ACCESS_TOKEN" = "null" ] || [ -z "$ACCESS_TOKEN" ]; then
    echo "Error: Could not get access token"
    echo "Auth Response: $AUTH_RESPONSE"
    exit 1
fi

echo "✓ Authentication successful!"
echo ""

# Step 4: Display tokens
echo "=== JWT TOKENS ==="
echo ""
echo "ACCESS TOKEN:"
echo "$ACCESS_TOKEN"
echo ""
echo "ID TOKEN:"
echo "$ID_TOKEN"
echo ""
echo "REFRESH TOKEN:"
echo "$REFRESH_TOKEN"
echo ""

# Step 5: Decode and display token claims
echo "=== TOKEN CLAIMS ==="
echo ""
echo "ACCESS TOKEN CLAIMS:"
echo $ACCESS_TOKEN | cut -d'.' -f2 | base64 -d 2>/dev/null | jq . || echo "Could not decode access token"
echo ""
echo "ID TOKEN CLAIMS:"
echo $ID_TOKEN | cut -d'.' -f2 | base64 -d 2>/dev/null | jq . || echo "Could not decode ID token"
echo ""

# Step 6: Test API endpoint (if API Gateway URL is provided)
echo "=== API TESTING ==="
echo ""
echo "To test your API endpoint, use the following curl command:"
echo ""
echo "curl -X GET \\"
echo "  'https://YOUR_API_GATEWAY_URL/dev/conversations' \\"
echo "  -H 'Authorization: Bearer $ACCESS_TOKEN' \\"
echo "  -H 'Content-Type: application/json'"
echo ""

# Save tokens to file for later use
TOKENS_FILE="/tmp/jwt_tokens_$(date +%Y%m%d_%H%M%S).json"
cat > $TOKENS_FILE << EOF
{
  "user_pool_id": "$USER_POOL_ID",
  "client_id": "$CLIENT_ID",
  "email": "$EMAIL",
  "access_token": "$ACCESS_TOKEN",
  "id_token": "$ID_TOKEN",
  "refresh_token": "$REFRESH_TOKEN",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

echo "Tokens saved to: $TOKENS_FILE"
echo ""
echo "=== SCRIPT COMPLETED SUCCESSFULLY ==="