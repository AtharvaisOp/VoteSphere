from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.conf import settings
import re
from .models import Election, Candidate, Vote


# ============= SECURE OTP AUTHENTICATION FORMS =============

class OTPRequestForm(forms.Form):
    """
    Form for requesting OTP via email.
    Validates college email format.
    """
    email = forms.EmailField(
        max_length=200,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'student@college.edu',
            'autofocus': True
        }),
        label='College Email Address'
    )
    
    def clean_email(self):
        """Validate email matches college pattern"""
        email = self.cleaned_data.get('email')
        
        # Check if email matches college pattern
        pattern = settings.COLLEGE_EMAIL_PATTERN
        if not re.search(pattern, email, re.IGNORECASE):
            raise ValidationError(
                f'Please use a valid college email address (e.g., @college.edu)'
            )
        
        return email.lower()


class OTPVerifyForm(forms.Form):
    """
    Form for verifying OTP code.
    """
    email = forms.EmailField(
        widget=forms.HiddenInput()
    )
    
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000000',
            'maxlength': '6',
            'pattern': '[0-9]{6}',
            'autofocus': True,
            'style': 'text-align: center; font-size: 24px; letter-spacing: 8px;'
        }),
        label='Enter 6-Digit OTP Code'
    )
    
    def clean_otp_code(self):
        """Validate OTP is numeric"""
        otp = self.cleaned_data.get('otp_code')
        
        if not otp.isdigit():
            raise ValidationError('OTP must contain only numbers')
        
        return otp


# ============= VOTING FORMS =============

class VoteForm(forms.Form):
    """
    Form for casting votes in an election.
    Dynamically generates radio buttons for each position.
    """
    def __init__(self, *args, **kwargs):
        election = kwargs.pop('election', None)
        super().__init__(*args, **kwargs)
        
        if election:
            # Group candidates by position
            positions = {}
            for candidate in election.candidates.all():
                if candidate.position not in positions:
                    positions[candidate.position] = []
                positions[candidate.position].append(candidate)
            
            # Create a field for each position
            for position, candidates in positions.items():
                choices = [(c.id, c.name) for c in candidates]
                self.fields[position] = forms.ChoiceField(
                    choices=choices,
                    widget=forms.RadioSelect,
                    label=dict(Candidate.POSITION_CHOICES).get(position, position),
                    required=True
                )


# ============= ADMIN FORMS =============

class ElectionForm(forms.ModelForm):
    """Form for creating and editing elections (admin only)"""
    class Meta:
        model = Election
        fields = ['title', 'description', 'start_date', 'end_date', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class CandidateForm(forms.ModelForm):
    """Form for adding and editing candidates (admin only)"""
    class Meta:
        model = Candidate
        fields = ['election', 'name', 'position', 'description', 'photo']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


# Legacy registration form - deprecated in secure mode
class UserRegistrationForm(UserCreationForm):
    """Extended registration form with custom validation (DEPRECATED)"""
    email = forms.EmailField(
        required=True,
        help_text="Enter a valid email address"
    )
    first_name = forms.CharField(
        max_length=100, 
        required=True,
        help_text="Enter your first name"
    )
    last_name = forms.CharField(
        max_length=100, 
        required=True,
        help_text="Enter your last name"
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
    
    def clean_email(self):
        """Validate email - check if already exists"""
        email = self.cleaned_data.get('email')
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "❌ This email address is already registered. Please use a different email."
            )
        
        return email

