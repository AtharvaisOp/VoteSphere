from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
import re


class Election(models.Model):
    """
    Represents a college election event.
    Each election has a title, description, and active time window.
    """
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_manually_ended = models.BooleanField(default=False, help_text="Admin manually ended this election")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def is_ongoing(self):
        """Check if the election is currently active and within time window"""
        now = timezone.now()
        return self.is_active and not self.is_manually_ended and self.start_date <= now <= self.end_date
    
    def has_ended(self):
        """Check if the election has ended (either by time or manually)"""
        return self.is_manually_ended or timezone.now() > self.end_date
    
    def has_started(self):
        """Check if the election has started"""
        return timezone.now() >= self.start_date
    
    def clean(self):
        """Validate that end_date is after start_date"""
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValidationError('End date must be after start date.')


class Candidate(models.Model):
    """
    Represents a candidate running for a position in an election.
    """
    POSITION_CHOICES = [
        ('president', 'President'),
        ('vice_president', 'Vice President'),
        ('secretary', 'Secretary'),
        ('treasurer', 'Treasurer'),
        ('cultural_head', 'Cultural Head'),
        ('sports_head', 'Sports Head'),
    ]
    
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='candidates')
    name = models.CharField(max_length=200)
    position = models.CharField(max_length=50, choices=POSITION_CHOICES)
    description = models.TextField(help_text="Candidate's manifesto or bio")
    photo = models.ImageField(upload_to='candidates/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['position', 'name']
        unique_together = ['election', 'name', 'position']  # Prevent duplicate candidates
    
    def __str__(self):
        return f"{self.name} - {self.get_position_display()} ({self.election.title})"
    
    def get_vote_count(self):
        """Return the number of votes this candidate has received"""
        # Note: After encryption update, this will need to decrypt votes
        # For now, we'll handle this in views with decryption logic
        from .crypto_utils import decrypt_vote
        
        count = 0
        for vote in self.election.votes.all():
            try:
                # Only decrypt if election has ended
                if self.election.has_ended():
                    vote_data = decrypt_vote(vote.encrypted_vote)
                    # vote_data is a dict of {position: candidate_id}
                    if str(self.id) in vote_data.values() or self.id in vote_data.values():
                        count += 1
            except Exception:
                # If decryption fails or election not ended, skip
                pass
        
        return count


# ============= SECURE AUTHENTICATION MODELS =============

class OTPToken(models.Model):
    """
    Temporary storage for email OTPs.
    OTPs expire after OTP_EXPIRATION_MINUTES and can only be used once.
    """
    email = models.EmailField()
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"OTP for {self.email} - {'Used' if self.is_used else 'Active'}"
    
    def is_expired(self):
        """Check if OTP has expired"""
        from django.conf import settings
        from datetime import timedelta
        
        expiration_time = self.created_at + timedelta(minutes=settings.OTP_EXPIRATION_MINUTES)
        return timezone.now() > expiration_time
    
    def is_valid(self):
        """Check if OTP is valid (not used and not expired)"""
        return not self.is_used and not self.is_expired()


class Voter(models.Model):
    """
    Anonymous voter tracking using hashed identities.
    No personally identifiable information is stored.
    """
    voter_hash = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Track which elections this voter has voted in
    has_voted_in = models.ManyToManyField(Election, related_name='voters', blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Voter {self.voter_hash[:8]}..."
    
    def has_voted_in_election(self, election):
        """Check if this voter has already voted in the given election"""
        return self.has_voted_in.filter(id=election.id).exists()


# ============= SECURE VOTE MODEL =============

class Vote(models.Model):
    """
    Encrypted, anonymous vote with blockchain-style integrity.
    
    Security features:
    - No link to identifiable user (uses voter_hash)
    - Vote data is RSA-encrypted
    - Hash chain prevents tampering
    - Admin cannot view or modify votes
    """
    # Anonymous voter identification
    voter_hash = models.CharField(max_length=64, db_index=True)
    
    # Encrypted vote data (JSON string encrypted with RSA public key)
    # Format when decrypted: {"position1": candidate_id1, "position2": candidate_id2, ...}
    encrypted_vote = models.TextField()
    
    # Blockchain-style hash chain
    previous_hash = models.CharField(max_length=64, default="GENESIS")
    current_hash = models.CharField(max_length=64, unique=True, db_index=True)
    
    # Metadata
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='votes')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']  # Chronological order for hash chain
        indexes = [
            models.Index(fields=['election', 'voter_hash']),
            models.Index(fields=['election', 'timestamp']),
        ]
    
    def __str__(self):
        return f"Encrypted Vote in {self.election.title} at {self.timestamp}"
    
    def clean(self):
        """Validation before saving"""
        # Verify hash chain integrity if this is not the first vote
        if self.previous_hash != "GENESIS":
            # Check that previous_hash exists
            previous_vote = Vote.objects.filter(
                election=self.election,
                current_hash=self.previous_hash
            ).first()
            
            if not previous_vote:
                raise ValidationError(
                    f'Invalid hash chain: previous_hash {self.previous_hash} not found'
                )

