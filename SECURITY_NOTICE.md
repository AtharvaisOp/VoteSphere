# Security Notice

## Important Security Files

### RSA Keys
- **Public Key**: `keys/public_key.pem` (committed to repo)
- **Private Key**: `../secure_keys/private_key.pem` (NEVER commit this!)

### Database Backup
- Old database backed up to: `db.sqlite3.backup`
- Contains old vote data (not compatible with new encrypted system)

### .gitignore Entries
Add these to your `.gitignore`:
```
secure_keys/
*.backup
db.sqlite3
```

## What Changed
The Vote model has been completely redesigned:
- Votes are now RSA-encrypted
- Hash chain integrity prevents tampering
- No User foreign key (anonymous voting)
- Voter identities are hashed (SHA-256)

**⚠️ Old votes cannot be migrated** due to fundamental model changes.
