"""
Management command to generate RSA key pair for vote encryption.
Usage: python manage.py generate_rsa_keys
"""

from django.core.management.base import BaseCommand
from elections.crypto_utils import generate_rsa_keypair, save_keys_to_files


class Command(BaseCommand):
    help = 'Generate RSA key pair for vote encryption and save to configured paths'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Generating RSA-2048 key pair...'))
        
        # Generate keys
        private_pem, public_pem = generate_rsa_keypair(key_size=2048)
        
        # Save to files
        save_keys_to_files(private_pem, public_pem)
        
        self.stdout.write(self.style.SUCCESS('✅ RSA key pair generated successfully!'))
        self.stdout.write(self.style.WARNING('⚠️  SECURITY REMINDER:'))
        self.stdout.write('   - Keep the private key secure')
        self.stdout.write('   - Never commit keys to version control')
        self.stdout.write('   - Add secure_keys/ to .gitignore')
