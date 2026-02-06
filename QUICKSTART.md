# VoteSphere Secure Election System - Quick Start Guide

## 🚀 System is Ready!

The VoteSphere election system has been upgraded with military-grade security. Your server is running at **http://localhost:8000**

---

## 📋 Quick Start (First Time)

### 1. Create Admin Account
```powershell
# Open new terminal (keep server running in background)
cd c:\Users\athar\OneDrive\Desktop\VoteSphere-main
python manage.py createsuperuser

# Enter:
# Username: admin
# Email: admin@votesphere.edu
# Password: [your choice]
```

### 2. Access the System

**For Voters (OTP Login):**
- Navigate to: http://localhost:8000/auth/request-otp/
- Enter college email (e.g., `student@test.edu`)
- Check terminal/console for OTP code
- Enter code to login

**For Admins (Manage Elections):**
- Navigate to: http://localhost:8000/admin-panel/
- Login with admin Django account (not OTP)

**Django Admin (Advanced):**
- Navigate to: http://localhost:8000/admin/
- Full Django admin panel

---

## 🧪 Test the Security Features

### Test 1: OTP Authentication ✅
1. Go to http://localhost:8000/auth/request-otp/
2. Enter: `student@university.edu`
3. Check server terminal for OTP (6-digit code)
4. Enter OTP → Should login successfully

### Test 2: Encrypted Votes ✅
After voting, check encryption in Django shell:
```python
python manage.py shell

>>> from elections.models import Vote
>>> v = Vote.objects.last()
>>> print(v.encrypted_vote)  # Long encrypted string
>>> print(v.voter_hash)      # SHA-256 hash
```

### Test 3: Admin Tampering Prevention ✅
1. Login to admin: http://localhost:8000/admin/
2. **Verify**: Vote model is NOT in the admin list
3. Try direct access: http://localhost:8000/admin/elections/vote/
4. **Expected**: 404 error (model not registered)

---

## 🔐 Security Highlights

| Feature | Status |
|---------|--------|
| **OTP Email Authentication** | ✅ Implemented |
| **Voter Identity Hashing (SHA-256)** | ✅ Implemented |
| **RSA-2048 Vote Encryption** | ✅ Implemented |
| **Hash Chain Integrity** | ✅ Implemented |
| **Admin Tampering Prevention** | ✅ Implemented |
| **Decryption Only After Election Ends** | ✅ Implemented |

---

## 📁 Important Files

### Security Keys (DO NOT COMMIT!)
- **Private Key**: `c:\Users\athar\secure_keys\private_key.pem`
- **Public Key**: `c:\Users\athar\OneDrive\Desktop\VoteSphere-main\keys\public_key.pem`

### Backups
- **Old Database**: `db.sqlite3.backup` (contains old vote data)
- **New Database**: `db.sqlite3` (fresh with encrypted votes)

### Documentation
- **Implementation Plan**: See artifacts
- **Walkthrough**: See artifacts
- **Security Notice**: `SECURITY_NOTICE.md`

---

## ⚙️ Configuration

### Email Settings (Development)
Currently using **console backend** - OTPs print to terminal.

To use real email, edit `votesphere/settings.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
# ... (see settings.py for full config)
```

### College Email Pattern
Current: `@.*\.edu$` (any .edu domain)

To restrict, edit `votesphere/settings.py`:
```python
COLLEGE_EMAIL_PATTERN = r'@yourcollege\.edu$'
```

---

## 🎯 Next Steps

1. **Create Admin User** (see step 1 above)
2. **Create Test Election**:
   - Login to admin panel
   - Create election with start/end dates
   - Add candidates for each position
3. **Test Voting Flow**:
   - Use OTP login as voter
   - Cast votes
   - Verify encryption in database
4. **End Election & View Results**:
   - Manually end election from admin
   - View decrypted results
   - Verify hash chain integrity

---

## 🆘 Troubleshooting

**OTP not received?**
- Check server terminal/console (using console backend in dev)
- OTP printed directly to terminal

**Can't login to admin panel?**
- Need to create Django superuser first (see Quick Start #1)
- Admin panel != voter OTP auth

**Votes not decrypting?**
- Election must be ended first (manually or by date)
- Hash chain must be valid
- Private key must exist: `c:\Users\athar\secure_keys\private_key.pem`

**Migration errors?**
- Database was reset for breaking model changes
- Old votes in `db.sqlite3.backup` (cannot migrate)
- Elections/candidates need to be recreated

---

## ✨ You're All Set!

The system is fully operational and ready for secure elections!

**Server Status**: 🟢 Running at http://localhost:8000

For detailed documentation, see the walkthrough artifact.
