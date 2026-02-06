# VoteSphere - College Election Management System

A secure, transparent, and fair digital voting platform for college elections, aligned with UN SDG 16 (Peace, Justice, and Strong Institutions).

## Features

### � **Military-Grade Security**
- **OTP Email Authentication**: Passwordless login using 6-digit one-time passwords
- **Anonymous Voting**: Voter identities hashed (SHA-256) and original emails deleted after verification
- **RSA-2048 Encryption**: All votes encrypted with public key cryptography before storage
- **Hash Chain Integrity**: Blockchain-style tamper detection for vote records
- **Admin Tampering Prevention**: Vote data completely hidden from admin interface
- **Post-Election Decryption**: Votes only decryptable after election ends

### 📊 **Election Management**
- **Transparent Results**: Real-time vote counting with visual charts and statistics
- **Multi-Position Elections**: Support for multiple positions (President, Treasurer, etc.)
- **Automatic Vote Counting**: Instant result generation with integrity verification
- **Vote Integrity Checks**: Hash chain validation before displaying results
- **Manual Election Control**: Admins can manually end elections if needed

### 🌍 **User Experience**
- **Easy to Use**: Intuitive interface for both voters and administrators
- **Mobile Responsive**: Vote from any device during the election window
- **Email Support**: Supports both .edu and .ac.in college domains
- **Dark/Light Theme**: Automatic theme based on system preferences
- **Real-Time Feedback**: Instant validation and error messages

### 🎯 **Fair & Democratic**
- **One Vote Per Election**: Cryptographically enforced via voter hash tracking
- **Equal Opportunity**: All candidates displayed fairly with photos and descriptions
- **SDG 16 Aligned**: Supporting Peace, Justice, and Strong Institutions
- **Audit Trail**: Complete vote history with timestamps (encrypted)

## Tech Stack

- **Backend**: Django 6.0.1 (MVT Architecture)
- **Database**: SQLite (easily extensible to PostgreSQL/MySQL)
- **Authentication**: Custom OTP system with email delivery
- **Email Service**: SendGrid API for OTP delivery
- **Encryption**: RSA-2048 (cryptography library)
- **Hashing**: SHA-256 for voter identity and hash chains
- **Visualization**: Matplotlib for result charts
- **Frontend**: Django templates with modern HTML/CSS/JavaScript

## Installation

1. **Clone or download the project**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Generate RSA keys for vote encryption**:
   ```bash
   python manage.py generate_rsa_keys
   ```

4. **Configure SendGrid (for OTP emails)**:
   - Update `SENDGRID_API_KEY` in `settings.py`
   - Or set environment variable: `SENDGRID_API_KEY=your-key-here`
   - Verify your sender email in SendGrid dashboard

5. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser (admin)**:
   ```bash
   python manage.py createsuperuser
   ```

7. **Test SendGrid email (optional)**:
   ```bash
   python test_sendgrid.py
   ```

8. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

9. **Access the application**:
   - Home page: http://localhost:8000/
   - Voter OTP Login: http://localhost:8000/auth/request-otp/
   - Admin panel: http://localhost:8000/admin/
   - Custom admin dashboard: http://localhost:8000/admin-panel/

## Usage

### For Administrators (Staff Users)

1. Login to the admin panel at `/admin/` using Django superuser credentials
2. Navigate to custom admin dashboard at `/admin-panel/`
3. Create new elections with title, description, and time window
4. Add candidates for each position with photos and descriptions
5. Monitor election status (votes are encrypted and hidden)
6. End elections manually or wait for automatic end
7. View decrypted results after election ends (with integrity check)

**Note**: Admins CANNOT view individual votes - they are RSA-encrypted and removed from admin interface for security.

### For Voters (Students)

1. Navigate to `/auth/request-otp/`
2. Enter your college email (supports .edu and .ac.in domains)
3. Check your email for 6-digit OTP code (expires in 5 minutes)
4. Enter OTP to login (your email is then hashed and deleted)
5. View active elections in dashboard
6. Browse candidates for each position
7. Cast your vote (encrypted before storage)
8. Vote only once per election (enforced via voter hash)
9. View results after election ends

## Project Structure

```
VoteSphere/
├── votesphere/              # Main project directory
│   ├── settings.py          # Project configuration (includes SendGrid, RSA paths)
│   ├── urls.py              # Root URL configuration
│   └── wsgi.py              # WSGI configuration
├── elections/               # Main app for election management
│   ├── models.py            # Election, Candidate, Vote, Voter, OTPToken models
│   ├── views.py             # OTP auth, voting, results with decryption
│   ├── urls.py              # App URL patterns (OTP routes)
│   ├── forms.py             # OTP forms and voting forms
│   ├── admin.py             # Admin panel (Vote model removed)
│   ├── utils.py             # Chart generation and hash chain validation
│   ├── crypto_utils.py      # RSA encryption/decryption, hashing, validation
│   ├── management/
│   │   └── commands/
│   │       └── generate_rsa_keys.py  # RSA key generation command
│   └── templates/           # HTML templates
│       ├── auth/            # OTP login templates
│       ├── voter/           # Voter dashboard and voting
│       └── admin_panel/     # Admin templates
├── static/                  # CSS, JS, videos
├── media/                   # Candidate photos, generated charts
├── keys/                    # RSA public key (committed)
├── ../secure_keys/          # RSA private key (OUTSIDE project, NOT committed)
├── test_sendgrid.py         # SendGrid email test script
└── manage.py                # Django management script
```

## Security Features

### 🔒 **Authentication & Privacy**
- **OTP-Based Login**: No passwords stored, reducing attack surface
- **Email Hashing**: SHA-256 hash of email + secret salt, original email deleted
- **Session Security**: Voter sessions tracked via hashed identity only
- **International Support**: Accepts both .edu and .ac.in college domains

### 🔐 **Vote Encryption**
- **RSA-2048 Public Key**: All votes encrypted before database storage
- **Private Key Security**: Stored outside project directory, never accessible via Django
- **Unreadable Storage**: Vote data completely encrypted in database
- **Decryption Only After Election**: Results decrypted only when election officially ends

### ⛓️ **Blockchain-Style Integrity**
- **Hash Chains**: Each vote linked to previous with SHA-256 hash
- **Tamper Detection**: Any modification breaks the chain → results blocked
- **Genesis Block**: First vote has `previous_hash = "GENESIS"`
- **Automatic Validation**: Chain verified before every result display

### 🛡️ **Admin Tampering Prevention**
- **No Vote Admin**: Vote model completely removed from Django admin
- **Encrypted Display**: Even if accessed, votes are RSA-encrypted
- **Integrity Required**: Results display fails if hash chain is broken
- **Audit Protection**: Tampering immediately detected by hash validation

### 📧 **Email Security**
- **SendGrid Integration**: Professional email delivery via API
- **OTP Expiration**: 6-digit codes expire after 5 minutes
- **Single Use**: Each OTP can only be used once
- **Rate Limiting**: Built-in protection against spam (via SendGrid)

### 💾 **Database Security**
- **No PII Storage**: No personally identifiable information retained
- **Anonymous Votes**: No link between voter identity and vote content
- **Encrypted Data**: All vote payloads RSA-encrypted
- **Hash Chain Verification**: Tamper-evident storage

## SDG 16 Alignment

VoteSphere supports UN Sustainable Development Goal 16 (Peace, Justice, and Strong Institutions) by:

- Promoting inclusive and participatory decision-making
- Ensuring transparent and accountable electoral processes
- Building trust in democratic institutions
- Providing equal access to voting for all students
- Strengthening student governance through technology

## License

This project is created for educational purposes as part of SDG 16 awareness and implementation.

## Support

For issues or questions, please refer to the SDG 16 page at `/sdg16/` for more information about the project's mission and goals.
