# LIFE T1a — Cloudflare Workers AI setup

Purpose: enable the final real-data E2E test without changing LIFE code.

## Cloudflare

1. Open Cloudflare Dashboard → Workers AI → Use REST API.
2. Create a Workers AI API Token using the provided template.
3. If creating a custom token, grant the account permissions `Workers AI - Read` and `Workers AI - Edit`.
4. Copy the Cloudflare Account ID.
5. Store the token only in Railway Variables; never commit it to GitHub.

## Railway variables

```env
AI_PROVIDER=cloudflare
CLOUDFLARE_ACCOUNT_ID=<account id>
CLOUDFLARE_API_TOKEN=<secret token>
CLOUDFLARE_MODEL=@cf/zai-org/glm-4.7-flash
```

## Verification

After deployment:

```text
GET /health
  ai_provider = cloudflare
  ai_enabled = true
  ai_data_usage = not_used_for_training
```

Only after these conditions are true should a real Google account be connected and the first live E2E test executed.

## Security

The token is server-side only. The frontend never receives it. LIFE blocks Gmail/Calendar source reads when the privacy gate is not satisfied.