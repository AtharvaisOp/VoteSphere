"""
Postmark Email Test Script
Run this to verify your Postmark API token is working correctly.
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'votesphere.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_postmark():
    """Test Postmark using Django's email backend"""
    print("=" * 60)
    print("Testing Postmark Email Delivery")
    print("=" * 60)
    print(f"API Token: {settings.POSTMARK_API_TOKEN[:20]}...")
    print(f"From Email: {settings.DEFAULT_FROM_EMAIL}")
    print(f"Email Backend: {settings.EMAIL_BACKEND}")
    print(f"Test Mode: {settings.POSTMARK_TEST_MODE}")
    print()
    
    try:
        # Send test email
        result = send_mail(
            subject='VoteSphere - Postmark Test Email',
            message='This is a test email from VoteSphere to verify Postmark configuration.\n\n'
                    'If you received this, your Postmark integration is working correctly!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['atharva.ghuge24@sakec.ac.in'],  # Change to your email
            fail_silently=False,
        )
        
        if result == 1:
            print("✅ SUCCESS! Email sent successfully via Postmark!")
            print("📧 Check your inbox at: atharva.ghuge24@sakec.ac.in")
            print("\nNext steps:")
            print("1. Check your email inbox (and spam folder)")
            print("2. Verify the sender email in Postmark dashboard if not already done")
            print("3. Add sender signature at: https://account.postmarkapp.com/signatures")
            print("4. Update DEFAULT_FROM_EMAIL in settings.py if needed")
        else:
            print("⚠️  Email may not have been sent (result: {})".format(result))
            
    except Exception as e:
        print("❌ ERROR sending email:")
        print(str(e))
        print("\nCommon issues:")
        print("1. Sender email not verified in Postmark (add Sender Signature)")
        print("2. Invalid API token")
        print("3. API token doesn't have permission to send from this address")
        print("\nAdd sender signature: https://account.postmarkapp.com/signatures")
        print("View activity: https://account.postmarkapp.com/servers/{server}/streams/outbound")

if __name__ == '__main__':
    test_postmark()
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print("\n💡 Tips:")
    print("- Postmark has excellent deliverability (better than SendGrid for transactional emails)")
    print("- Check the Activity tab in Postmark dashboard to see email status")
    print("- Use Message Streams to organize different types of emails")
