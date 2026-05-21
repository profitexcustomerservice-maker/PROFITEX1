# Email Configuration Setup Guide for OTP

## Problem
OTP emails are not being delivered because SMTP credentials are not configured.

## Root Cause
The system requires `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` environment variables to be set for email delivery to work.

## Solution Options

### Option 1: Gmail (Recommended for Testing)

#### Step 1: Enable 2FA on Google Account
1. Go to https://myaccount.google.com/security
2. Under "Signing in to Google", enable "2-Step Verification"

#### Step 2: Generate App Password
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and "Other (Custom name)"
3. Name it "NovaProfit" and click "Generate"
4. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

#### Step 3: Set Environment Variables
Add these to your `.env` file or system environment:

```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_16_char_app_password
```

**IMPORTANT**: Remove spaces from the App Password when setting the environment variable.
Example: `EMAIL_HOST_PASSWORD=abcdefghijklmnop`

#### Step 4: Restart Server
Stop and restart your Django server for environment variables to take effect.

#### Step 5: Test Email Sending
Run the test script:
```bash
python test_email.py
```

### Option 2: SendGrid (Recommended for Production)

#### Step 1: Create SendGrid Account
1. Go to https://sendgrid.com/
2. Sign up for a free account

#### Step 2: Get API Key
1. Go to Settings > API Keys
2. Create API Key with "Mail Send" permissions
3. Copy the API key

#### Step 3: Configure Django
Update settings in `.env`:
```bash
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your_sendgrid_api_key
```

### Option 3: Mailgun

#### Step 1: Create Mailgun Account
1. Go to https://www.mailgun.com/
2. Sign up for free trial

#### Step 2: Get SMTP Credentials
1. Go to Settings > Domain Settings
2. Copy SMTP username and password

#### Step 3: Configure Django
Update settings in `.env`:
```bash
EMAIL_HOST=smtp.mailgun.org
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_smtp_username
EMAIL_HOST_PASSWORD=your_smtp_password
```

### Option 4: Amazon SES (Enterprise)

#### Step 1: Create AWS Account
1. Go to https://aws.amazon.com/ses/
2. Create AWS account

#### Step 2: Verify Email Domain
1. In SES console, verify your sending domain

#### Step 3: Get SMTP Credentials
1. Generate SMTP credentials in SES console

#### Step 4: Configure Django
Update settings in `.env`:
```bash
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_smtp_username
EMAIL_HOST_PASSWORD=your_smtp_password
```

## Testing

### Manual Test
Run the email test script:
```bash
python test_email.py
```

### Full OTP Flow Test
1. Register a new account
2. Check console for debug output
3. Enter OTP code from email
4. Verify successful login

## Troubleshooting

### Gmail: "Authentication failed"
- Ensure 2FA is enabled
- Use App Password (not regular password)
- Remove spaces from App Password

### Gmail: "Connection timed out"
- Check firewall settings
- Ensure port 587 is not blocked
- Try port 465 with SSL

### "Email not received"
- Check spam/junk folder
- Verify recipient email is correct
- Check email server logs

### "SSL error"
- Ensure EMAIL_USE_TLS=True
- Check SSL/TLS settings
- Try different port

## Security Best Practices

1. **Never commit credentials to Git**
   - Add `.env` to `.gitignore`
   - Use environment variables in production

2. **Use App Passwords for Gmail**
   - Never use regular Gmail password
   - Generate separate App Password for each app

3. **Production Email Services**
   - Use SendGrid, Mailgun, or Amazon SES for production
   - Gmail has daily sending limits

4. **Monitor Email Reputation**
   - Track bounce rates
   - Monitor spam complaints
   - Use proper SPF/DKIM records

## Current Status

✅ Email backend configured (SMTP)
✅ Error logging implemented
✅ Test script created
⏳ Awaiting SMTP credentials from user

## Next Steps

1. Choose an email service (Gmail, SendGrid, etc.)
2. Set up credentials following the guide above
3. Add credentials to `.env` file
4. Restart Django server
5. Run `python test_email.py` to verify
6. Test full OTP registration/login flow
