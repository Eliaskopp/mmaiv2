# MMAi V2 — Production Cutover Checklist

## Pre-Cutover

- [ ] V1 archive confirmed at `~/mmai-v1-archive/` (DB dump + code)
- [ ] V2 backend tests passing: `cd backend && uv run pytest`
- [ ] V2 frontend builds cleanly: `cd frontend && npm run build`
- [ ] `backend/.env` reviewed:
  - [ ] `JWT_SECRET` rotated from dev value
  - [ ] `DAILY_MESSAGE_LIMIT=30`
  - [ ] `ALLOWED_ORIGINS` includes `https://www.mmai.coach`
  - [ ] `APP_URL=https://www.mmai.coach`
  - [ ] `RESEND_API_KEY` set
  - [ ] `GROK_API_KEY` set
  - [ ] `DEBUG=false`
- [ ] PM2 ecosystem config has `log_date_format`
- [ ] Playwright smoke test passes against staging (`chat.mmai.coach`)

## SSL Certificate

```bash
# If www.mmai.coach is not already on the cert:
sudo certbot --nginx -d mmai.coach -d www.mmai.coach -d chat.mmai.coach
```

## Nginx Cutover

```bash
# 1. Deploy production config
sudo cp docs/nginx-www-mmai-coach.conf /etc/nginx/sites-available/www-mmai-coach
sudo ln -sf /etc/nginx/sites-available/www-mmai-coach /etc/nginx/sites-enabled/

# 2. Remove V1 config (the old www.mmai.coach server block)
#    IMPORTANT: Identify the exact file — do NOT remove chat.mmai.coach config
sudo rm /etc/nginx/sites-enabled/<v1-config-name>

# 3. Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

## PM2 Process

```bash
# V2 is already running as mmai-v2 — verify
pm2 status

# If ecosystem.config.js was updated:
pm2 reload ecosystem.config.js --env production

# Verify health
curl -s https://www.mmai.coach/api/health | python3 -m json.tool
```

## Post-Cutover Verification

- [ ] `https://www.mmai.coach` loads the V2 SPA
- [ ] `https://mmai.coach` redirects to `https://www.mmai.coach`
- [ ] `https://chat.mmai.coach` still works (staging, unchanged)
- [ ] Login / register flow works on production
- [ ] Chat sends a message and receives AI response
- [ ] Email verification sends via Resend
- [ ] Journal, Notes, Stats, Recovery, Profile pages load
- [ ] API health check: `curl https://www.mmai.coach/api/health`

## Rollback Plan

If something goes wrong:

```bash
# 1. Point www.mmai.coach back to V1 archive
#    (restore V1 nginx config from ~/mmai-v1-archive/)
sudo cp ~/mmai-v1-archive/nginx/<v1-config> /etc/nginx/sites-available/
sudo ln -sf /etc/nginx/sites-available/<v1-config> /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 2. chat.mmai.coach remains unaffected (separate config)
```

## Important: No Redirect Between Tiers

- `chat.mmai.coach` = Staging (stays as-is)
- `www.mmai.coach` = Production
- Both point to the same V2 backend on port 8001
- Do NOT add any redirect from chat → www or www → chat
