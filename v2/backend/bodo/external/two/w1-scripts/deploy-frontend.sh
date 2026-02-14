#!/bin/bash
# Deploy Frontend to W1.SEDAILY.AI
# =================================

set -e
source "$(dirname "$0")/config.sh"

echo "========================================="
echo "   W1 Frontend Deployment"
echo "   Target: https://w1.sedaily.ai"
echo "========================================="

# Step 1: Build frontend
build_frontend() {
    log_info "Building frontend..."
    
    cd "$FRONTEND_DIR"
    
    # Check if npm dependencies are installed
    if [ ! -d "node_modules" ]; then
        log_info "Installing dependencies..."
        npm install
    fi
    
    # Build the project
    log_info "Running build..."
    ./node_modules/.bin/vite build
    
    if [ -d "dist" ]; then
        log_info "Build successful!"
    else
        log_error "Build failed - dist directory not created"
        exit 1
    fi
}

# Step 2: Deploy to S3
deploy_to_s3() {
    log_info "Deploying to S3..."

    # First sync all files (this handles deletions)
    aws s3 sync "$FRONTEND_DIR/dist" \
        "s3://${FRONTEND_BUCKET}" \
        --delete \
        --region "${AWS_REGION}" \
        --cache-control "public, max-age=3600"

    # Re-upload JS files with correct MIME type
    log_info "Setting correct MIME types for JS files..."
    for file in "$FRONTEND_DIR/dist/assets"/*.js; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            aws s3 cp "$file" "s3://${FRONTEND_BUCKET}/assets/$filename" \
                --region "${AWS_REGION}" \
                --content-type "application/javascript" \
                --cache-control "public, max-age=31536000" \
                --quiet
        fi
    done

    # Re-upload CSS files with correct MIME type
    log_info "Setting correct MIME types for CSS files..."
    for file in "$FRONTEND_DIR/dist/assets"/*.css; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            aws s3 cp "$file" "s3://${FRONTEND_BUCKET}/assets/$filename" \
                --region "${AWS_REGION}" \
                --content-type "text/css" \
                --cache-control "public, max-age=31536000" \
                --quiet
        fi
    done

    # Re-upload HTML with correct MIME type
    log_info "Setting correct MIME type for HTML..."
    aws s3 cp "$FRONTEND_DIR/dist/index.html" "s3://${FRONTEND_BUCKET}/index.html" \
        --region "${AWS_REGION}" \
        --content-type "text/html; charset=utf-8" \
        --cache-control "public, max-age=3600" \
        --quiet

    log_info "S3 deployment complete"
}

# Step 3: Invalidate CloudFront cache
invalidate_cloudfront() {
    log_info "Creating CloudFront invalidation..."
    
    local invalidation_id=$(aws cloudfront create-invalidation \
        --distribution-id "${CLOUDFRONT_ID}" \
        --paths "/*" \
        --region "${AWS_REGION}" \
        --query 'Invalidation.Id' \
        --output text)
    
    log_info "Invalidation created: ${invalidation_id}"
    echo "  Note: Cache invalidation may take 5-10 minutes to complete"
}

# Step 4: Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check S3 bucket
    local file_count=$(aws s3 ls "s3://${FRONTEND_BUCKET}" --recursive --region "${AWS_REGION}" | wc -l)
    log_info "Files uploaded to S3: ${file_count}"
    
    # Check website
    local status=$(curl -s -o /dev/null -w "%{http_code}" "https://${DOMAIN}")
    if [ "$status" == "200" ]; then
        log_info "Website responding: HTTP ${status} ✅"
    else
        log_warning "Website status: HTTP ${status}"
    fi
}

# Main execution
main() {
    # Check if in correct directory
    if [ ! -f "$FRONTEND_DIR/package.json" ]; then
        log_error "Frontend directory not found. Please run from project root."
        exit 1
    fi
    
    # Check current environment configuration
    log_info "Current configuration:"
    echo "  API URL: $(grep VITE_API_BASE_URL "$FRONTEND_DIR/.env" | cut -d= -f2)"
    echo "  WS URL: $(grep VITE_WS_URL "$FRONTEND_DIR/.env" | cut -d= -f2)"
    echo ""
    
    # Auto-confirm if -y flag is passed
    if [[ "$1" != "-y" ]]; then
        read -p "Continue with deployment? (y/n): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Deployment cancelled"
            exit 0
        fi
    fi
    
    # Execute deployment steps
    build_frontend
    echo ""
    deploy_to_s3
    echo ""
    invalidate_cloudfront
    echo ""
    verify_deployment
    
    echo ""
    echo "========================================="
    echo "✅ W1 Frontend Deployment Complete!"
    echo "========================================="
    echo ""
    echo "Access the site: https://${DOMAIN}"
    echo ""
    echo "Note: CloudFront cache invalidation in progress."
    echo "Full update may take 5-10 minutes."
}

main "$@"