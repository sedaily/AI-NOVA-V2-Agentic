#!/bin/bash
# Deploy Backend Code to W1 Lambda Functions
# ===========================================

set -e
source "$(dirname "$0")/config.sh"

echo "========================================="
echo "   W1 Backend Deployment"
echo "   Target: w1.sedaily.ai Lambda Functions"
echo "========================================="

# Step 1: Package Lambda code
package_lambda() {
    log_info "Packaging Lambda code..."
    
    cd "$BACKEND_DIR"
    
    # Clean previous package
    rm -rf package lambda-deployment.zip 2>/dev/null || true
    
    # Install dependencies
    log_info "Installing dependencies..."
    pip install -r requirements.txt -t ./package --quiet
    
    # Copy source code
    cd package
    cp -r ../handlers .
    cp -r ../services .
    cp -r ../src .
    cp -r ../lib .
    cp -r ../utils .
    
    # Clean up
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    
    # Create zip
    log_info "Creating deployment package..."
    zip -r ../lambda-deployment.zip . -q
    cd ..
    
    local size=$(du -h lambda-deployment.zip | cut -f1)
    log_info "Package created: lambda-deployment.zip (${size})"
}

# Step 2: Deploy to Lambda functions
deploy_lambda() {
    log_info "Deploying to Lambda functions..."
    
    local success_count=0
    local total=${#LAMBDA_FUNCTIONS[@]}
    
    for function in "${LAMBDA_FUNCTIONS[@]}"; do
        echo -n "  Updating ${function}..."
        
        if aws lambda update-function-code \
            --function-name "${function}" \
            --zip-file fileb://lambda-deployment.zip \
            --region "${AWS_REGION}" \
            --output text --query 'LastModified' > /dev/null 2>&1; then
            echo " ✅"
            ((success_count++))
        else
            echo " ❌"
            log_error "Failed to update ${function}"
        fi
    done
    
    echo ""
    log_info "Deployed ${success_count}/${total} functions successfully"
}

# Step 3: Update environment variables
update_env_vars() {
    log_info "Updating environment variables..."
    
    local env_vars="Variables={
        USE_ANTHROPIC_API=true,
        ANTHROPIC_SECRET_NAME=${SECRET_NAME},
        ANTHROPIC_MODEL_ID=${ANTHROPIC_MODEL},
        AI_PROVIDER=anthropic_api,
        FALLBACK_TO_BEDROCK=true,
        ANTHROPIC_MAX_TOKENS=${ANTHROPIC_MAX_TOKENS},
        ANTHROPIC_TEMPERATURE=${ANTHROPIC_TEMPERATURE}
    }"
    
    for function in "${LAMBDA_FUNCTIONS[@]}"; do
        echo -n "  Configuring ${function}..."
        
        if aws lambda update-function-configuration \
            --function-name "${function}" \
            --environment "${env_vars}" \
            --region "${AWS_REGION}" \
            --output text --query 'LastModified' > /dev/null 2>&1; then
            echo " ✅"
        else
            echo " ❌"
        fi
    done
}

# Main execution
main() {
    # Check if in correct directory
    if [ ! -f "$BACKEND_DIR/requirements.txt" ]; then
        log_error "Backend directory not found. Please run from project root."
        exit 1
    fi
    
    # Execute deployment steps
    package_lambda
    echo ""
    deploy_lambda
    echo ""
    
    # Ask about environment variables
    read -p "Update environment variables? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        update_env_vars
    fi
    
    echo ""
    echo "========================================="
    echo "✅ W1 Backend Deployment Complete!"
    echo "========================================="
    echo ""
    echo "Next steps:"
    echo "1. Test the service at https://w1.sedaily.ai"
    echo "2. Monitor logs: ./monitor-logs.sh"
    echo "3. Run tests: ./test-service.sh"
}

main "$@"