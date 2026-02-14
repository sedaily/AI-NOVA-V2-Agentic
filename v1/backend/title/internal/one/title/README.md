# Title Service (Internal/One)

AI-powered title generation service.

> **Last Updated**: 2025-01-14
> **Purpose**: Internal use (Direct chat without login/sidebar)

---

## Deployment Resources

| Resource | Value |
|----------|-------|
| **CloudFront URL** | https://d1jjxbf1f82fxa.cloudfront.net |
| **CloudFront ID** | `ELNOVAGFGH16I` |
| **S3 Bucket** | `nexus-single-title-frontend` |
| **Region** | us-east-1 |

### Quick Deploy

```bash
cd frontend
npm run build
aws s3 sync dist/ s3://nexus-single-title-frontend/ --delete --region us-east-1
aws cloudfront create-invalidation --distribution-id ELNOVAGFGH16I --paths "/*"
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
