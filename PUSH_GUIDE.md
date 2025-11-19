# Push to Remote Repository Guide

⚠️ **READ THIS BEFORE PUSHING** - Your repository contains fixed security issues with rewritten git history.

## Current Status

- Local commits: 5 (includes security fixes)
- Remote status: Not yet pushed
- Git history: Rewritten (API keys removed)

## ⚠️ Critical: Credential Rotation

**STOP! Before pushing, you MUST rotate exposed Firebase credentials:**

### Exposed Credentials (NOW REMOVED FROM GIT)
- Firebase Project: `havital-dev`
- Firebase Project: `paceriz-prod`

### Credential Rotation Steps

1. **Go to Firebase Console**
   - https://console.firebase.google.com

2. **For Each Project (havital-dev & paceriz-prod)**

   a) **Regenerate API Keys**
   - Settings → Project Settings → Web API Keys
   - Delete old keys
   - Create new API keys
   - Save the new values

   b) **Restrict API Keys**
   - Select each new API key
   - Add Application restrictions:
     - HTTP referrers: localhost:*, yourdomain.com
   - Add API restrictions:
     - Cloud Firestore API only
     - Firebase Authentication

   c) **Rotate Service Accounts**
   - Settings → Service Accounts
   - For each service account:
     - Create new key
     - Delete old key
     - Update deployment configurations

   d) **Review Security Rules**
   - Firestore → Rules
   - Update to use least privilege principle
   - Example:
     ```javascript
     rules_version = '2';
     service cloud.firestore {
       match /databases/{database}/documents {
         match /{document=**} {
           allow read, write: if request.auth != null;
         }
       }
     }
     ```

   e) **Enable 2FA & API Key Restrictions**
   - Enable 2-factor authentication
   - Restrict API key access by IP/referrer
   - Monitor Firebase console daily for 7 days

3. **Monitor for Unauthorized Access**
   - Review Firebase Authentication logs
   - Check Firestore access logs
   - Monitor API usage anomalies

## Step 1: Prepare Local Environment

```bash
# Create .env.development with new credentials
cd frontend
cp .env.example .env.development

# Edit with your NEW Firebase credentials
# (from the freshly generated keys above)
nano .env.development
```

### .env.development Template
```env
VITE_FIREBASE_DEV_API_KEY=<NEW_KEY_FROM_FIREBASE>
VITE_FIREBASE_DEV_AUTH_DOMAIN=havital-dev.firebaseapp.com
VITE_FIREBASE_DEV_PROJECT_ID=havital-dev
VITE_FIREBASE_DEV_STORAGE_BUCKET=havital-dev.firebasestorage.app
VITE_FIREBASE_DEV_MESSAGING_SENDER_ID=<FROM_FIREBASE>
VITE_FIREBASE_DEV_APP_ID=<FROM_FIREBASE>
VITE_FIREBASE_DEV_MEASUREMENT_ID=<FROM_FIREBASE>
```

## Step 2: Verify Local Setup

```bash
# Test that your app builds with new credentials
npm install
npm run build

# If successful, you're ready to push
```

## Step 3: Add Remote Repository

If you haven't set up a remote yet:

```bash
# HTTPS (if you have GitHub token)
git remote add origin https://github.com/YOUR_USERNAME/subscription_cli.git

# Or SSH (if you have SSH keys configured)
git remote add origin git@github.com:YOUR_USERNAME/subscription_cli.git

# Verify remote was added
git remote -v
```

## Step 4: Push with Force (History Rewrite)

Since git history was rewritten to remove secrets, use:

```bash
# Push with --force-with-lease (safer than --force)
git push --force-with-lease origin main

# If the above fails and you're sure no one else pushed:
git push --force origin main
```

### ⚠️ Important Notes About Force Push

- **--force-with-lease**: Safer option, fails if remote has new commits
- **--force**: Dangerous, will overwrite any remote changes
- **Only safe if**: No one else has cloned the old repository yet
- **Already pushed?**: Contact admin, may need to purge git history from GitHub

## Step 5: Verify Remote Push

```bash
# Verify push was successful
git log --oneline
git log origin/main --oneline

# Should see:
# ad0f66a Add security incident report and guidelines
# 591254c Improve .gitignore for environment files
# 6e22bc6 Add environment setup documentation
# 295be31 Security fix: Remove hardcoded Firebase API keys
# 7674df6 Initial commit: Subscription CLI Management System

# Verify no secrets in remote
git log -p origin/main | grep -i "AIza" || echo "✅ No API keys in remote history"
```

## Step 6: Clean Up (Optional But Recommended)

If you want to be extra safe and ensure no stray .env files exist:

```bash
# Remove any .env files from working directory
rm frontend/.env.development  # if you cloned from somewhere

# Verify .gitignore is protecting them
git check-ignore frontend/.env*
```

## Step 7: Team Communication

After pushing, notify your team:

```
🔒 SECURITY UPDATE - Repository History Rewritten

1. Git history has been rewritten to remove hardcoded API keys
2. Firebase credentials have been rotated
3. To pull the new history:
   git fetch origin
   git reset --hard origin/main

4. Each developer needs to create local .env.development:
   cp frontend/.env.example frontend/.env.development
   # and fill in credentials

5. Read SECURITY.md for security best practices
```

## Troubleshooting

### "git push --force-with-lease" rejected
**Reason**: Remote has commits not in local history
**Solution**:
```bash
# Fetch remote first
git fetch origin
# If remote has new commits, you can't force push
# Contact repo admin about coordinating the update
```

### ".env.development" still showing in git
**Reason**: File was previously tracked
**Solution**:
```bash
git rm --cached frontend/.env.development
git commit -m "Stop tracking .env.development"
git push origin main
```

### "git filter-repo" not found
**Reason**: Tool not installed
**Solution**:
```bash
# On macOS
brew install git-filter-repo

# On Linux
pip install git-filter-repo

# Then re-run the filter
```

## Security Checklist

Before and after pushing:

```
Before Push:
- [ ] Rotated all Firebase API keys
- [ ] Created new .env.development locally
- [ ] Verified app builds with new credentials
- [ ] Checked no .env files are tracked
- [ ] Verified no secrets in git log

After Push:
- [ ] Pushed to origin main with --force-with-lease
- [ ] Verified remote has no API keys
- [ ] Team members have cloning instructions
- [ ] Monitored Firebase console for 24 hours
- [ ] Updated deployment environments
```

## Additional Resources

- [SECURITY.md](./SECURITY.md) - Full security incident report
- [frontend/ENV_SETUP.md](./frontend/ENV_SETUP.md) - Environment setup guide
- [Firebase Security Guide](https://firebase.google.com/docs/projects/security/guides)
- [Git-filter-repo Documentation](https://github.com/newren/git-filter-repo)

---

**Last Updated**: 2025-11-19
**Status**: Ready for Push (After Credential Rotation)
