# Secrets Governance

**Purpose:** Define how secrets, environment variables, API keys, and configuration values should be managed across GitHub Actions, n8n, Streamlit, Supabase, and Python.

**Last reviewed:** 2026-05-14  
**Status:** Initial governance baseline  
**Scope:** Repository-wide secret and environment variable handling

---

## 1. Core Rule

Real secret values must never be committed to the repository.

This includes:

- API keys
- Supabase service role keys
- webhook tokens
- database credentials
- provider credentials
- bearer tokens
- private URLs containing credentials

Allowed in the repository:

- placeholder values
- environment variable names
- `.env.example` files with dummy values
- documentation describing where secrets are stored

---

## 2. Secret Classes

| Class | Examples | Risk Level | Storage Location |
|---|---|---|---|
| Class 1: Critical | Supabase service role key, API provider secrets, OpenAI key, FMP key | High | GitHub Secrets, n8n Credentials, Streamlit Secrets |
| Class 2: Sensitive | Webhook tokens, notification credentials, Telegram bot token | Medium/High | GitHub Secrets, n8n Credentials |
| Class 3: Configuration | feature flags, non-secret URLs, table names, mode toggles | Low/Medium | GitHub Variables, `.env.example`, config docs |

---

## 3. Storage Rules by System

### GitHub Actions

Use GitHub repository secrets for:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_ANON_KEY`
- `FMP_API_KEY`
- `TWELVEDATA_API_KEY`
- `TAVILY_API_KEY`
- `OPENAI_API_KEY`
- `HUGGINGFACE_API_KEY`
- notification/webhook secrets

Do not hardcode these in workflow YAML.

### n8n

Use n8n credentials or secure variables for:

- API provider credentials
- Supabase headers
- webhook credentials
- notification tokens

Avoid storing real secrets directly in exported workflow JSON.

If a JSON export contains placeholder values such as `FMP_key` or `Supabase_key`, confirm they are placeholders before committing.

### Streamlit

Use Streamlit secrets or environment variables for:

- Supabase URL
- Supabase anon key
- read-only dashboard credentials

Streamlit should not use service-role keys unless there is a specific and reviewed reason.

### Python

Python should read secrets from environment variables.

Preferred pattern:

```python
import os

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
```

Avoid:

```python
SUPABASE_SERVICE_ROLE_KEY = "real_key_here"
```

---

## 4. Environment Variable Contract

Each production workflow or script should document required environment variables.

Suggested table format:

| Variable | Required By | Required? | Secret Class | Purpose | Storage |
|---|---|---|---|---|---|
| `SUPABASE_URL` | Python, Streamlit, GitHub Actions | Yes | Class 3 | Supabase project URL | GitHub Secrets / Streamlit Secrets |
| `SUPABASE_SERVICE_ROLE_KEY` | Python write jobs | Yes | Class 1 | Write access to Supabase | GitHub Secrets |
| `SUPABASE_ANON_KEY` | Streamlit read jobs | Yes | Class 1/2 | Read access under RLS | Streamlit Secrets |
| `FMP_API_KEY` | Ingestion jobs | Yes | Class 1 | Financial Modeling Prep API | GitHub Secrets / n8n Credentials |
| `TWELVEDATA_API_KEY` | Market data jobs | Conditional | Class 1 | Twelve Data API | GitHub Secrets / n8n Credentials |
| `TAVILY_API_KEY` | Research/news workflows | Conditional | Class 1 | Tavily search API | GitHub Secrets / n8n Credentials |
| `OPENAI_API_KEY` | LLM summarization/scoring | Conditional | Class 1 | OpenAI API | GitHub Secrets / n8n Credentials |
| `HUGGINGFACE_API_KEY` | Sentiment workflows | Conditional | Class 1 | Hugging Face inference | GitHub Secrets / n8n Credentials |

This table should be expanded as the workflow registry is created.

---

## 5. `.env.example` Policy

A `.env.example` file may be added with placeholders only.

Example:

```text
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=replace_with_anon_key
SUPABASE_SERVICE_ROLE_KEY=replace_with_service_role_key
FMP_API_KEY=replace_with_fmp_key
TWELVEDATA_API_KEY=replace_with_twelvedata_key
TAVILY_API_KEY=replace_with_tavily_key
OPENAI_API_KEY=replace_with_openai_key
HUGGINGFACE_API_KEY=replace_with_huggingface_key
```

Never commit `.env` files containing real values.

---

## 6. Secret Review Checklist

Before committing:

1. Search for `key`, `token`, `secret`, `Bearer`, `apikey`, `Authorization`.
2. Check exported n8n JSON for credential values.
3. Check Python constants for hardcoded secrets.
4. Check YAML files for hardcoded secrets.
5. Check Streamlit files for embedded Supabase keys.
6. Confirm `.env` is ignored.
7. Confirm `.env.example` contains placeholders only.

---

## 7. Recommended `.gitignore` Entries

Confirm these are present:

```text
.env
.env.*
!.env.example
.streamlit/secrets.toml
*.local
```

Be careful: `.env.*` can accidentally ignore `.env.example`; the exception line should preserve it.

---

## 8. Rotation Policy

Suggested baseline:

| Secret Type | Rotation Frequency | Trigger for Immediate Rotation |
|---|---|---|
| Supabase service role key | Every 6-12 months | Any suspected leak or accidental commit |
| API provider keys | Every 6-12 months | Unusual usage, billing spike, accidental exposure |
| Webhook tokens | Every 6 months | Workflow exposure or unknown caller |
| Notification tokens | Every 6-12 months | Bot/channel compromise |

Record rotations in a private operational note, not in public repo if it exposes sensitive timing or values.

---

## 9. Incident Response for Suspected Exposure

If a secret is accidentally committed:

1. Revoke or rotate the secret immediately.
2. Replace the secret in GitHub/n8n/Streamlit/Supabase.
3. Check recent API usage or database access logs.
4. Remove the secret from current files.
5. Consider repository history cleanup if the repository is public.
6. Document the incident in a private operational log.

Do not merely delete the line and continue using the same key.

---

## 10. Current Near-Term Actions

1. Create `.env.example` with placeholders only.
2. Create workflow registry and list required secrets per workflow.
3. Review n8n JSON exports for placeholder vs real secret values.
4. Align n8n credential names with GitHub secret names where practical.
5. Keep service-role keys out of Streamlit unless explicitly reviewed.
