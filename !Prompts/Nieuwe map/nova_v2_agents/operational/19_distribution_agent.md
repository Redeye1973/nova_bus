# 19. Distribution Agent

## Doel
Pakt gevalideerde city packages en andere NOVA producten en distribueert ze naar juiste consumers (NORA, FINN, externe klanten).

## Scope
- City packages naar consumer apps
- Asset library updates
- Product releases (game builds, updates)
- Client deliverables (voor B2B klanten)

## Functionaliteit

**1. Package Versioning**
- Semantic versioning
- Changelog generation
- Migration notes

**2. Upload Management**
- MinIO voor internal storage
- CDN distribution voor consumer apps
- Direct client delivery (voor B2B)

**3. Consumer Notification**
- Apps checken versioning endpoint
- Notify architects van nieuwe deliverables
- Marketing emails voor product releases

**4. Access Control**
- Per klant entitlements
- License enforcement
- Usage tracking

**5. Analytics**
- Download counts
- User activity per package
- Popular vs unused content

## Cursor Prompt

```
Bouw een NOVA v2 Distribution Agent:

1. Python service `distribution/versioner.py`:
   - SemVer version management
   - Compare met previous version
   - Generate diff + changelog
   - Tag in git

2. Python service `distribution/uploader.py`:
   - Upload naar MinIO buckets
   - Bucket structure: 
     - city_packages/{postcode}/{version}/
     - game_builds/{product}/{version}/
     - client_deliverables/{client_id}/{project}/
   - Generate signed URLs voor downloads
   - Checksum verification

3. Python service `distribution/notifier.py`:
   - Per consumer type andere notification:
     - Consumer apps: webhook naar version check endpoint
     - B2B clients: email met download link
     - Internal: Discord/Telegram
   - Template-based messaging

4. Python service `distribution/access_control.py`:
   - PostgreSQL table: entitlements
   - Fields: client_id, product, version, expires_at
   - Check bij download request
   - Log access attempts

5. Python service `distribution/analytics.py`:
   - Track downloads, views, usage
   - Generate reports per product
   - Identify trends (populair, stervend)
   - Dashboard integration

6. API endpoints voor consumers:
   - GET /api/v1/versions/{product} → latest version info
   - GET /api/v1/download/{product}/{version} → signed URL
   - POST /api/v1/usage → track gebruik
   - GET /api/v1/entitlements → user's toegang

7. B2B client portal (simple web):
   - Login per client
   - Zie beschikbare deliverables
   - Download history
   - Usage statistics
   - Support ticket submission

8. License validation library:
   - Embed in consumer apps
   - Check entitlement bij startup
   - Graceful degradation bij expired

9. N8n workflow voor release process:
   - Trigger: version approved by juries
   - Upload → Update DB → Notify → Monitor rollout
   - Rollback capability bij issues

Gebruik Python 3.11, FastAPI, PostgreSQL, MinIO SDK,
SendGrid/SMTP voor email, Discord webhooks.
```

## Distribution Targets

**Consumer Apps (public):**
- NORA rijtrainer updates via auto-update mechanism
- City package downloads binnen app
- Game updates via Steam/mobile app stores

**B2B Clients (licensed):**
- Architect bureaus met abonnement
- Gemeenten met FINN licentie
- Film productie met historische bakes

**Developer Tools (internal):**
- Asset libraries voor Nova team gebruik
- Pipeline updates
- Documentation

## Release Tiers

**Canary (10% rollout):**
- Eerste uur na release
- Monitor errors extra scherp
- Kan snel rollback

**Gradual (25%, 50%, 100%):**
- Over 24 uur
- Check metrics per fase
- Halt bij anomalies

**Full (100%):**
- Pas na canary succes
- Marketing communication
- Support team alerted

## Integration Points

- **Triggered by**: Bake Orchestrator na succesvolle jury validation
- **Integrates met**: Cost Guard voor bandwidth, Monitor voor health
- **Serves**: Alle NOVA consumer apps + B2B clients

## Test Scenario's

1. Nieuwe Hoogeveen v1.1 bake → distribute naar NORA → users get update
2. FINN klant deliverable → secure link naar client → download met tracking
3. Rollback scenario → previous version served snel
4. Unauthorized access attempt → logged en blocked

## Success Metrics

- Distribution success rate: > 99%
- Mean time to consumer (post-approval): < 10 min
- B2B delivery reliability: 100%
- Rollback time bij issues: < 15 min
