"""
Cryptographic utilities for secure voting system.

This module provides RSA encryption/decryption, voter identity hashing,
and blockchain-style hash chain validation for vote integrity.
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from django.conf import settings


def generate_rsa_keypair(key_size: int = 2048) -> Tuple[bytes, bytes]:
    """
    Generate RSA key pair for vote encryption.
    
    Args:
        key_size: RSA key size in bits (default: 2048)
    
    Returns:
        Tuple of (private_key_pem, public_key_pem) as bytes
    """
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend()
    )
    
    # Serialize private key to PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Get public key and serialize to PEM format
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return private_pem, public_pem


def save_keys_to_files(private_pem: bytes, public_pem: bytes):
    """
    Save RSA keys to files as configured in settings.
    
    Args:
        private_pem: Private key in PEM format
        public_pem: Public key in PEM format
    """
    # Create directories if they don't exist
    public_key_path = Path(settings.RSA_PUBLIC_KEY_PATH)
    private_key_path = Path(settings.RSA_PRIVATE_KEY_PATH)
    
    public_key_path.parent.mkdir(parents=True, exist_ok=True)
    private_key_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write keys to files
    with open(public_key_path, 'wb') as f:
        f.write(public_pem)
    
    with open(private_key_path, 'wb') as f:
        f.write(private_pem)
    
    print(f"✅ Public key saved to: {public_key_path}")
    print(f"✅ Private key saved to: {private_key_path}")
    print(f"⚠️  IMPORTANT: Secure the private key! Never commit it to version control.")


def load_public_key():
    """Load and return the public key for encryption."""
    with open(settings.RSA_PUBLIC_KEY_PATH, 'rb') as f:
        public_pem = f.read()
    
    return serialization.load_pem_public_key(public_pem, backend=default_backend())


def load_private_key():
    """Load and return the private key for decryption."""
    with open(settings.RSA_PRIVATE_KEY_PATH, 'rb') as f:
        private_pem = f.read()
    
    return serialization.load_pem_private_key(
        private_pem,
        password=None,
        backend=default_backend()
    )


def encrypt_vote(vote_data: dict) -> str:
    """
    Encrypt vote data using RSA public key.
    
    Args:
        vote_data: Dictionary containing vote information
                   e.g., {'candidate_id': 123, 'position': 'president'}
    
    Returns:
        Base64-encoded encrypted vote string
    """
    # Convert vote data to JSON string
    vote_json = json.dumps(vote_data, sort_keys=True)
    vote_bytes = vote_json.encode('utf-8')
    
    # Load public key
    public_key = load_public_key()
    
    # Encrypt using RSA-OAEP padding
    encrypted_bytes = public_key.encrypt(
        vote_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    # Return as base64-encoded string for storage
    import base64
    return base64.b64encode(encrypted_bytes).decode('utf-8')


def decrypt_vote(encrypted_vote: str) -> dict:
    """
    Decrypt vote data using RSA private key.
    
    Args:
        encrypted_vote: Base64-encoded encrypted vote string
    
    Returns:
        Dictionary containing decrypted vote data
    """
    import base64
    
    # Decode from base64
    encrypted_bytes = base64.b64decode(encrypted_vote.encode('utf-8'))
    
    # Load private key
    private_key = load_private_key()
    
    # Decrypt using RSA-OAEP padding
    decrypted_bytes = private_key.decrypt(
        encrypted_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    # Convert back to dictionary
    vote_json = decrypted_bytes.decode('utf-8')
    return json.loads(vote_json)


def generate_voter_hash(email: str) -> str:
    """
    Generate SHA-256 hash of voter email with salt.
    This creates an anonymous, non-reversible voter identifier.
    
    Args:
        email: Voter's email address
    
    Returns:
        Hexadecimal hash string (64 characters)
    """
    # Combine email with secret salt
    data = f"{email}{settings.VOTER_SALT}".encode('utf-8')
    
    # Generate SHA-256 hash
    hash_obj = hashlib.sha256(data)
    return hash_obj.hexdigest()


def generate_vote_hash(encrypted_vote: str, previous_hash: str, timestamp: datetime) -> str:
    """
    Generate SHA-256 hash for vote in the hash chain.
    
    Args:
        encrypted_vote: Encrypted vote data
        previous_hash: Hash of the previous vote (or "GENESIS" for first vote)
        timestamp: Timestamp of the vote
    
    Returns:
        Hexadecimal hash string (64 characters)
    """
    # Combine all components
    timestamp_str = timestamp.isoformat()
    data = f"{encrypted_vote}{previous_hash}{timestamp_str}".encode('utf-8')
    
    # Generate SHA-256 hash
    hash_obj = hashlib.sha256(data)
    return hash_obj.hexdigest()


def validate_vote_chain(election) -> Tuple[bool, Optional[str]]:
    """
    Validate the integrity of the entire vote hash chain for an election.
    
    This implements blockchain-style integrity verification:
    - Each vote's hash must be correctly calculated from its data
    - Each vote must reference the correct previous vote's hash
    - The chain must be unbroken from GENESIS to the last vote
    
    Args:
        election: Election object to validate
    
    Returns:
        Tuple of (is_valid, error_message)
        - (True, None) if chain is valid
        - (False, error_message) if tampering detected
    """
    from .models import Vote
    
    # Get all votes for this election in chronological order
    votes = Vote.objects.filter(election=election).order_by('timestamp')
    
    if not votes.exists():
        # No votes yet - chain is valid (empty)
        return True, None
    
    expected_previous_hash = "GENESIS"
    
    for idx, vote in enumerate(votes):
        # Verify previous_hash matches expected
        if vote.previous_hash != expected_previous_hash:
            return False, f"Vote #{idx + 1}: previous_hash mismatch. Expected '{expected_previous_hash}', got '{vote.previous_hash}'"
        
        # Recalculate current_hash
        calculated_hash = generate_vote_hash(
            vote.encrypted_vote,
            vote.previous_hash,
            vote.timestamp
        )
        
        # Verify current_hash matches calculated
        if vote.current_hash != calculated_hash:
            return False, f"Vote #{idx + 1}: current_hash mismatch. Vote data has been tampered with!"
        
        # Update expected previous hash for next vote
        expected_previous_hash = vote.current_hash
    
    return True, None
