# Security Guidelines & Incident Report

## 🚨 Incident: Hardcoded Firebase API Keys (RESOLVED)

### Summary
Firebase API keys and sensitive configuration were accidentally hardcoded in `frontend/src/config/environments.ts` and committed to git history.

### Timeline
- **Discovered**: 2025-11-19
- **Resolved**: 2025-11-19

### Actions Taken

#### 1. Immediate Remediation
- ✅ Removed all hardcoded API keys from source code
- ✅ Migrated to environment variable configuration
- ✅ Cleaned git history using `git filter-repo`
- ✅ Updated `.gitignore` to prevent future commits

#### 2. Code Changes
- **Modified**: `frontend/src/config/environments.ts`
  - Removed hardcoded Firebase configuration
  - Implemented runtime environment variable loading
  - Added validation and warning for missing variables

- **Created**: `frontend/.env.example`
  - Template for required environment variables
  - Safe to commit and share
  - Clear documentation of all required keys

- **Created**: `frontend/ENV_SETUP.md`
  - Setup instructions for developers
  - Firebase Console navigation guide
  - Best practices documentation

#### 3. Git History Cleanup
```
Commits before: 2 (included sensitive data)
Commits after: 4 (cleaned and improved)

Removed from history:
- frontend/src/config/environments.ts (with hardcoded keys)
- frontend/.env.development (with real credentials)
```

### ⚠️ CRITICAL: Credentials That Were Exposed

These Firebase credentials were visible in git history and must be **immediately rotated**:

| Project | Type | Status |
|---------|------|--------|
| havital-dev | Development | **NEEDS ROTATION** |
| paceriz-prod | Production | **NEEDS ROTATION** |

### Required Actions

#### Step 1: Revoke Old Credentials ⚡ URGENT
1. Go to [Firebase Console](https://console.firebase.google.com)
2. For each project (havital-dev, paceriz-prod):
   - Select the project
   - Go to Settings → Service Accounts
   - Regenerate all service account keys
   - Update API restrictions on web API keys
   - Review and tighten Firebase Security Rules

#### Step 2: Generate New Credentials
1. In Firebase Console, go to Project Settings
2. Under "Web API Keys", copy the new credentials
3. Update `.env.development` and `.env.production` with new values

#### Step 3: Deploy New Configuration
1. Update all deployment environments
2. Verify new credentials are being used
3. Monitor Firebase console for any unusual activity

#### Step 4: Git Push with Force
```bash
# Since history was rewritten, force push to update remote
# WARNING: Only safe if no one else has cloned the old history
git push --force-with-lease origin main
```

### Preventive Measures

#### Environment Variable Management
- ✅ All sensitive config now loaded from environment
- ✅ `.env` files ignored by git (see `.gitignore`)
- ✅ `.env.example` template provided

#### Code Review
- Always check for hardcoded secrets before committing
- Look for patterns:
  - API keys/tokens in strings
  - Credentials in configuration files
  - Database connection strings

#### Git Hooks (Recommended)
Consider installing git hooks to detect secrets:

```bash
# Using git-secrets (recommended)
brew install git-secrets  # macOS
git secrets --install
git secrets --register-aws

# Or use detect-secrets
pip install detect-secrets
```

### Monitoring

#### Check for Unauthorized Access
1. Review Firebase Authentication logs
2. Check Firestore access logs for unusual patterns
3. Monitor API usage for unexpected spikes
4. Review user accounts for suspicious activity

#### Regular Audits
- [ ] Weekly: Check Firebase console for unauthorized API keys
- [ ] Monthly: Rotate credentials on a schedule
- [ ] Quarterly: Security audit of environment configuration

## General Security Best Practices

### 1. Secrets Management

**DO:**
- Use environment variables for all secrets
- Use `.env.example` as template with empty values
- Store actual `.env` files locally (never commit)
- Rotate credentials regularly
- Use different credentials for dev/staging/prod

**DON'T:**
- Hardcode secrets in source code
- Commit `.env` files to git
- Share credentials via email or chat
- Use same credentials across environments
- Leave old credentials enabled after rotation

### 2. Firebase Security Rules

**Recommended Rules:**
```javascript
// Only allow authenticated users
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if request.auth != null;
    }
  }
}
```

### 3. API Key Restrictions

In Firebase Console, restrict API keys to:
- Specific referrer domains
- Specific APIs (Firestore, Auth only)
- Specific environments (dev/prod/staging)

### 4. Code Review Checklist

Before committing code:
```
[ ] No hardcoded API keys, tokens, or passwords
[ ] No Firebase credentials in code
[ ] All .env files are in .gitignore
[ ] Environment variables have defaults or warnings
[ ] Documentation shows secure setup
[ ] Secrets are loaded from environment at runtime
```

### 5. Incident Response

If you discover exposed credentials:
1. **IMMEDIATELY** rotate/revoke the credential
2. Notify all team members
3. Create git commits to clean history
4. Force push if necessary
5. Monitor for unauthorized access
6. Document incident and lessons learned

## Resources

- [Firebase Security Guide](https://firebase.google.com/docs/projects/security/guides)
- [OWASP Secrets Management](https://owasp.org/www-community/Data_Exposure)
- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)
- [git-secrets](https://github.com/awslabs/git-secrets)

## Contact & Escalation

For security incidents:
1. Document the issue immediately
2. Notify team leads
3. Follow incident response procedures
4. Create incident report

---

**Last Updated**: 2025-11-19
**Status**: Resolved (Credentials Rotation Pending)
