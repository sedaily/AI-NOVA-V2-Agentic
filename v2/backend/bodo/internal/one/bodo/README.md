# Bodo (Press Release) Service (Internal/One)

AI-powered press release generation service.

> **Last Updated**: 2026-01-24
> **Purpose**: Internal use (Direct chat without login/sidebar)

---

## Deployment Resources

| Resource | Value |
|----------|-------|
| **CloudFront URL** | https://d2emwatb21j743.cloudfront.net |
| **CloudFront ID** | `EDF1H6DB796US` |
| **S3 Bucket** | `bodo-frontend-20251204-230645dc` |
| **Region** | ap-northeast-2 |

### Quick Deploy

```bash
cd frontend
npm run build
aws s3 sync dist/ s3://bodo-frontend-20251204-230645dc/ --delete --region ap-northeast-2
aws cloudfront create-invalidation --distribution-id EDF1H6DB796US --paths "/*"
```

---

## Routes

- `/` → Redirects to `/11`
- `/11` → Engine 1
- `/22` → Engine 2

## Key Features (Internal Version)

- **No Login**: Immediate access
- **No Sidebar**: Clean UI
- **Direct Chat**: `/` redirects to `/11` automatically
