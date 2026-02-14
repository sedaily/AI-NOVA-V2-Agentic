# Proofreading Service (Internal/One)

AI-powered article proofreading and editing service.

## Deployment Resources

| Resource | Value |
|----------|-------|
| **CloudFront URL** | https://d1zig3y52jaq1s.cloudfront.net |
| **CloudFront ID** | `E1O9OA8UA34Z49` |
| **S3 Bucket** | `nexus-multi-frontend-20251204` |
| **Region** | ap-northeast-2 |

## Deployment

```bash
cd frontend
npm run build
aws s3 sync dist/ s3://nexus-multi-frontend-20251204/ --delete --region ap-northeast-2
aws cloudfront create-invalidation --distribution-id E1O9OA8UA34Z49 --paths "/*"
```

## Routes

- `/` → Redirects to `/11`
- `/11` → Engine 1
- `/22` → Engine 2
