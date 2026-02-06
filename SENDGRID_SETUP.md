# Postmark Email Integration Guide

## ✅ Configuration Complete!

Postmark has been integrated for OTP email delivery.

---

## 🔑 API Token Configuration

### Current Setup (Temporary - For Testing)
The API token is currently **hardcoded** in `settings.py` for immediate testing:
```
1c7b67b8-f528-449a-8141-260b71d5ae03
```

### ⚠️ Production Setup (Recommended)

**For production, use environment variables:**

#### Windows PowerShell:
```powershell
$env:POSTMARK_API_TOKEN="1c7b67b8-f528-449a-8141-260b71d5ae03"
```

#### Windows Command Prompt:
```cmd
set POSTMARK_API_TOKEN=1c7b67b8-f528-449a-8141-260b71d5ae03
```

#### Linux/Mac:
```bash
export POSTMARK_API_TOKEN='1c7b67b8-f528-449a-8141-260b71d5ae03'
```

---

## 📧 Postmark Configuration

### Email Settings (Updated in settings.py)
```python
EMAIL_BACKEND = 'postmark.django_backend.EmailBackend'
POSTMARK_API_TOKEN = '1c7b67b8-f528-449a-8141-260b71d5ae03'
POSTMARK_SENDER = 'VoteSphere <atharvaghuge2006@gmail.com>'
DEFAULT_FROM_EMAIL = 'VoteSphere <atharvaghuge2006@gmail.com>'
```

### Important: Sender Signature Verification

**Postmark requires sender signature verification!**

1. **Go to Postmark Dashboard:**
   - https://account.postmarkapp.com/signatures

2. **Add Sender Signature:**
   - Click "Add Sender Signature"
   - Enter: `atharvaghuge2006@gmail.com`
   - Verify via email confirmation sent to that address
   - Wait for approval (usually instant for Gmail)

3. **Alternative: Domain Authentication** (for production):
   - Authenticate your entire domain
   - Requires DNS configuration (SPF, DKIM records)
   - Better for production use

---

## 🧪 Testing Email Delivery

### Test 1: Quick Test Script
```bash
python test_sendgrid.py  # (renamed but works for Postmark too)
```

**Expected:** You should receive the email within seconds!

### Test 2: OTP Flow
1. Navigate to: http://localhost:8000/auth/request-otp/
2. Enter your email address
3. Click "Send OTP"
4. **Check your email inbox** for the OTP code
5. Enter the code to login

---

## 📊 Postmark Dashboard

Monitor email delivery:
- **Activity**: https://account.postmarkapp.com/servers/{server}/streams/outbound
- **Message Streams**: Organize transactional vs broadcast emails
- **Templates**: Create email templates (optional)

---

## 🔧 Troubleshooting

### Problem: Emails not being delivered

**Check 1: Sender Signature**
- Ensure sender email is verified at: https://account.postmarkapp.com/signatures
- Update `DEFAULT_FROM_EMAIL` and `POSTMARK_SENDER` to match verified email

**Check 2: API Token**
- Verify token at: https://account.postmarkapp.com/servers/{server}/credentials
- Ensure it's a **Server API Token** (not Account token)

**Check 3: Django Logs**
- Check server terminal for error messages
- Look for authentication or permission errors

**Check 4: Postmark Activity**
- Check Activity feed in Postmark dashboard
- Look for bounces, spam complaints, or delivery failures

### Problem: 401 Unauthorized Error

**Solution:**
- Verify you're using the correct API token
- Ensure the token is a **Server API Token**
- Check the token has permission to send emails

### Problem: 422 Unprocessable Entity

**Solutions:**
- Sender signature not verified → Add signature at dashboard
- Invalid "From" email → Must match verified signature
- Missing required fields → Check email headers

---

## 🚀 Switch Back to Console (For Testing)

To temporarily use console output instead of Postmark:

**Edit `settings.py`:**
```python
# Comment out Postmark
# EMAIL_BACKEND = 'postmark.django_backend.EmailBackend'

# Use console backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

---

## 🔒 Security Best Practices

1. ✅ **Never commit API tokens** to version control
2. ✅ **Use environment variables** in production
3. ✅ **Rotate API tokens** regularly
4. ✅ **Use separate servers** for dev/staging/production
5. ✅ **Monitor delivery** in Postmark dashboard

---

## 📈 Why Postmark?

Compared to SendGrid:
- ✅ **Better Deliverability**: Specialized in transactional emails
- ✅ **Simpler Setup**: No complex SMTP configuration
- ✅ **Cleaner API**: More reliable for Django
- ✅ **Better Support**: Excellent documentation
- ✅ **Message Streams**: Better email organization

---

## ✨ You're Ready!

Postmark is now configured for email delivery. OTPs will be sent to real email addresses!

**Next Steps:**
1. Verify your sender signature in Postmark: https://account.postmarkapp.com/signatures
2. Test OTP delivery with your email
3. Update `DEFAULT_FROM_EMAIL` if needed
4. Consider using environment variables for production
