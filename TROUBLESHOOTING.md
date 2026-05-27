# Troubleshooting — Wine Pair Content Intelligence Engine

---

## Setup check failures

### "config/service_account.json not found"

You haven't downloaded the service account key yet, or it's in the wrong place.

Fix: Follow SETUP.md → Step 2c. The file must be at `config/service_account.json` relative to the project root.

### "GSC access to https://thewinepairpodcast.com/ failed"

The service account email has not been granted access to your Search Console property.

Fix: Follow SETUP.md → Step 2d. The service account email looks like `winepair-intelligence@your-project.iam.gserviceaccount.com`.

### "YouTube API key invalid"

Either the key is wrong, the YouTube Data API v3 is not enabled in your Google Cloud project, or the key has been restricted to other APIs.

Fix: Check Google Cloud Console → APIs & Services → Library → confirm YouTube Data API v3 is enabled. If you restricted the key, make sure it allows YouTube Data API v3.

---

## Runtime errors

### "ImportError: google-api-python-client not installed"

Run: `pip install -r requirements.txt`

### "google.auth.exceptions.DefaultCredentialsError"

The service account JSON file is malformed or the path is wrong. Verify `config/service_account.json` contains valid JSON and the path in `.env` is correct.

### "HttpError 403: The caller does not have permission"

The service account does not have access to the Search Console property. Re-check SETUP.md → Step 2d.

### "feedparser: bozo exception"

A feed URL has changed or is temporarily unavailable. The system continues without it. Check `logs/` for details.

---

## GitHub Actions failures

### "Secret not found"

A required GitHub secret is missing. Go to repository Settings → Secrets and variables → Actions and verify all secrets from SETUP.md → Step 5b are present.

### "Push failed: permission denied"

The GitHub Actions workflow needs write permissions. Check repository Settings → Actions → General → Workflow permissions → set to "Read and write permissions".

### Database not committed after run

The workflow commits the database only if there are changes. If no new data was collected, there may be nothing to commit — this is normal.

---

## Getting help

If you hit an error not covered here, check `logs/` for the full error message and share it with Claude Code for diagnosis.
