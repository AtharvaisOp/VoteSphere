from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import logout
from django.contrib import messages
from django.utils import timezone
from django.db import IntegrityError, models
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from collections import defaultdict
import os
import random
import json

from .models import Election, Candidate, Vote, OTPToken, Voter
from .forms import VoteForm, ElectionForm, CandidateForm, OTPRequestForm, OTPVerifyForm
from .utils import generate_election_results_chart, generate_pie_chart, get_election_statistics
from .crypto_utils import (
    generate_voter_hash, 
    encrypt_vote, 
    decrypt_vote,
    generate_vote_hash,
    validate_vote_chain
)


# ============= Custom Decorators =============

def voter_session_required(view_func):
    """Decorator to require valid voter session (replaces @login_required)"""
    def wrapper(request, *args, **kwargs):
        voter_hash = request.session.get('voter_hash')
        if not voter_hash:
            messages.error(request, 'Please verify your email with OTP to access this page.')
            return redirect('request_otp')
        
        # Verify voter exists
        try:
            voter = Voter.objects.get(voter_hash=voter_hash)
            request.voter = voter  # Attach to request for easy access
        except Voter.DoesNotExist:
            messages.error(request, 'Invalid session. Please login again.')
            return redirect('request_otp')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


# ============= Public Views =============

def home(request):
    """Home page with hero section"""
    active_elections = Election.objects.filter(
        is_active=True, 
        start_date__lte=timezone.now(), 
        end_date__gte=timezone.now()
    )
    return render(request, 'home.html', {
        'active_elections': active_elections
    })


# ============= OTP Authentication Views =============

def request_otp(request):
    """Request OTP via email"""
    if request.method == 'POST':
        form = OTPRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            
            # Generate 6-digit OTP
            otp_code = str(random.randint(100000, 999999))
            
            # Save OTP to database
            OTPToken.objects.create(
                email=email,
                otp_code=otp_code
            )
            
            # Send email (or print to console in dev mode)
            try:
                send_mail(
                    subject='VoteSphere - Your OTP Code',
                    message=f'Your OTP code is: {otp_code}\n\nThis code will expire in {settings.OTP_EXPIRATION_MINUTES} minutes.\n\nIf you did not request this code, please ignore this email.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                messages.success(request, f'OTP sent to {email}. Please check your email.')
            except Exception as e:
                # In development with console backend, this is expected
                print(f"\n{'='*60}")
                print(f"OTP CODE FOR {email}: {otp_code}")
                print(f"{'='*60}\n")
                messages.success(request, f'OTP generated. Check the console for your code.')
            
            # Store email in session for verification page
            request.session['otp_email'] = email
            return redirect('verify_otp')
    else:
        form = OTPRequestForm()
    
    return render(request, 'auth/request_otp.html', {'form': form})


def verify_otp(request):
    """Verify OTP and create voter session"""
    email = request.session.get('otp_email')
    
    if not email:
        messages.error(request, 'Please request an OTP first.')
        return redirect('request_otp')
    
    if request.method == 'POST':
        form = OTPVerifyForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp_code']
            
            # Find matching OTP
            try:
                otp_token = OTPToken.objects.filter(
                    email=email,
                    otp_code=otp_code
                ).latest('created_at')
                
                # Verify OTP is valid
                if not otp_token.is_valid():
                    if otp_token.is_expired():
                        messages.error(request, 'OTP has expired. Please request a new one.')
                    else:
                        messages.error(request, 'This OTP has already been used.')
                    return redirect('request_otp')
                
                # Mark OTP as used
                otp_token.is_used = True
                otp_token.save()
                
                # Generate voter hash
                voter_hash = generate_voter_hash(email)
                
                # Create or get Voter
                voter, created = Voter.objects.get_or_create(voter_hash=voter_hash)
                
                # Delete email from OTP token (privacy)
                otp_token.email = '[REDACTED]'
                otp_token.save()
                
                # Clear email from session
                del request.session['otp_email']
                
                # Create voter session
                request.session['voter_hash'] = voter_hash
                
                messages.success(request, 'Email verified successfully! Welcome to VoteSphere.')
                return redirect('voter_dashboard')
                
            except OTPToken.DoesNotExist:
                messages.error(request, 'Invalid OTP code. Please try again.')
    else:
        form = OTPVerifyForm(initial={'email': email})
    
    return render(request, 'auth/verify_otp.html', {
        'form': form,
        'email': email
    })


def logout_view(request):
    """Custom logout view that clears voter session"""
    if 'voter_hash' in request.session:
        del request.session['voter_hash']
    logout(request)
    return render(request, 'auth/logout.html')


# ============= Voter Views =============

@voter_session_required
def voter_dashboard(request):
    """Dashboard for voters showing available elections and voting status"""
    now = timezone.now()
    voter = request.voter
    
    # Get ongoing elections
    ongoing_elections = Election.objects.filter(
        is_active=True,
        is_manually_ended=False,
        start_date__lte=now,
        end_date__gte=now
    )
    
    # Get upcoming elections
    upcoming_elections = Election.objects.filter(
        is_active=True,
        start_date__gt=now
    )
    
    # Get ended elections
    ended_elections = Election.objects.filter(
        (models.Q(end_date__lt=now) | models.Q(is_manually_ended=True)) & 
        models.Q(is_active=True)
    )
    
    # Check which elections voter has voted in
    voted_election_ids = voter.has_voted_in.values_list('id', flat=True)
    
    return render(request, 'voter/dashboard.html', {
        'ongoing_elections': ongoing_elections,
        'upcoming_elections': upcoming_elections,
        'ended_elections': ended_elections,
        'user_votes': voted_election_ids,  # For template compatibility
    })


@voter_session_required
def candidate_list(request, election_id):
    """Display all candidates for a specific election grouped by position"""
    election = get_object_or_404(Election, id=election_id)
    voter = request.voter
    
    # Group candidates by position
    positions = defaultdict(list)
    for candidate in election.candidates.all():
        positions[candidate.position].append(candidate)
    
    # Check if voter has already voted
    has_voted = voter.has_voted_in_election(election)
    
    return render(request, 'voter/candidates.html', {
        'election': election,
        'positions': dict(positions),
        'position_choices': Candidate.POSITION_CHOICES,
        'has_voted': has_voted,
    })


@voter_session_required
def cast_vote(request, election_id):
    """Handle the voting process with encryption"""
    election = get_object_or_404(Election, id=election_id)
    voter = request.voter
    
    # Check if election is ongoing
    if not election.is_ongoing():
        messages.error(request, 'This election is not currently active.')
        return redirect('voter_dashboard')
    
    # Check if voter has already voted
    if voter.has_voted_in_election(election):
        messages.warning(request, 'You have already voted in this election.')
        return redirect('candidate_list', election_id=election_id)
    
    if request.method == 'POST':
        form = VoteForm(request.POST, election=election)
        if form.is_valid():
            try:
                # Collect all votes (position -> candidate_id mapping)
                vote_data = {}
                for position, candidate_id in form.cleaned_data.items():
                    vote_data[position] = int(candidate_id)
                
                # Encrypt the vote data
                encrypted_vote = encrypt_vote(vote_data)
                
                # Get previous vote's hash (or GENESIS for first vote)
                last_vote = Vote.objects.filter(election=election).order_by('-timestamp').first()
                previous_hash = last_vote.current_hash if last_vote else "GENESIS"
                
                # Create timestamp
                timestamp = timezone.now()
                
                # Generate current hash
                current_hash = generate_vote_hash(encrypted_vote, previous_hash, timestamp)
                
                # Create vote record
                Vote.objects.create(
                    voter_hash=voter.voter_hash,
                    encrypted_vote=encrypted_vote,
                    previous_hash=previous_hash,
                    current_hash=current_hash,
                    election=election,
                    timestamp=timestamp
                )
                
                # Mark voter as having voted in this election
                voter.has_voted_in.add(election)
                
                messages.success(request, '✅ Your vote has been recorded securely and anonymously!')
                return redirect('voter_dashboard')
                    
            except Exception as e:
                messages.error(request, f'Error recording vote: {str(e)}')
                return redirect('voter_dashboard')
    else:
        form = VoteForm(election=election)
    
    # Group candidates by position for display
    positions = defaultdict(list)
    for candidate in election.candidates.all():
        positions[candidate.position].append(candidate)
    
    return render(request, 'voter/vote.html', {
        'election': election,
        'form': form,
        'positions': dict(positions),
        'position_choices': Candidate.POSITION_CHOICES,
    })


@voter_session_required
def election_results(request, election_id):
    """Display election results with charts (only if election has ended)"""
    election = get_object_or_404(Election, id=election_id)
    
    # Verify election has ended
    if not election.has_ended():
        messages.warning(request, 'Results will be available after the election ends.')
        return redirect('voter_dashboard')
    
    # Validate hash chain before showing results
    is_valid, error = validate_vote_chain(election)
    
    if not is_valid:
        # Show warning but continue displaying results (non-blocking)
        messages.warning(request, f'⚠️ Vote integrity warning: {error}. Results displayed but may have been tampered with.')
        integrity_valid = False
    else:
        integrity_valid = True
    
    # Decrypt and count votes
    vote_counts = defaultdict(lambda: defaultdict(int))
    
    for vote in election.votes.all():
        try:
            vote_data = decrypt_vote(vote.encrypted_vote)
            # vote_data is {position: candidate_id}
            for position, candidate_id in vote_data.items():
                vote_counts[position][int(candidate_id)] += 1
        except Exception as e:
            print(f"Error decrypting vote: {e}")
            continue
    
    # Generate charts if election has ended
    bar_chart_path = None
    pie_chart_path = None
    
    bar_chart_filename = f'election_{election.id}_bar_chart.png'
    pie_chart_filename = f'election_{election.id}_pie_chart.png'
    
    bar_chart_full_path = os.path.join(settings.MEDIA_ROOT, 'results', bar_chart_filename)
    pie_chart_full_path = os.path.join(settings.MEDIA_ROOT, 'results', pie_chart_filename)
    
    # Create results directory if it doesn't exist
    os.makedirs(os.path.join(settings.MEDIA_ROOT, 'results'), exist_ok=True)
    
    # Generate charts
    generate_election_results_chart(election, bar_chart_full_path)
    generate_pie_chart(election, pie_chart_full_path)
    
    bar_chart_path = f'{settings.MEDIA_URL}results/{bar_chart_filename}'
    pie_chart_path = f'{settings.MEDIA_URL}results/{pie_chart_filename}'
    
    # Get statistics
    stats = get_election_statistics(election)
    
    # Group candidates by position with vote counts
    positions = defaultdict(list)
    for candidate in election.candidates.all():
        positions[candidate.position].append({
            'candidate': candidate,
            'votes': candidate.get_vote_count()  # This now uses decryption
        })
    
    return render(request, 'voter/results.html', {
        'election': election,
        'positions': dict(positions),
        'position_choices': Candidate.POSITION_CHOICES,
        'bar_chart_path': bar_chart_path,
        'pie_chart_path': pie_chart_path,
        'stats': stats,
        'integrity_valid': integrity_valid,
    })


# ============= Admin Views (Staff only - using Django User auth) =============

def is_staff_user(user):
    """Check if user is staff/admin"""
    return user.is_staff or user.is_superuser


@user_passes_test(is_staff_user)
def admin_dashboard(request):
    """Admin dashboard for managing elections"""
    from django.contrib.auth.decorators import login_required
    
    elections = Election.objects.all()
    total_votes = Vote.objects.count()
    total_candidates = Candidate.objects.count()
    
    # Calculate results for each election
    for election in elections:
        # Only show results if election has ended
        if election.has_ended():
            results_by_position = defaultdict(list)
            for candidate in election.candidates.all():
                results_by_position[candidate.position].append({
                    'name': candidate.name,
                    'votes': candidate.get_vote_count()
                })
            # Sort candidates by votes (descending) within each position
            for position in results_by_position:
                results_by_position[position].sort(key=lambda x: x['votes'], reverse=True)
            
            election.results_by_position = dict(results_by_position)
        else:
            election.results_by_position = {}

    return render(request, 'admin_panel/dashboard.html', {
        'elections': elections,
        'total_votes': total_votes,
        'total_candidates': total_candidates,
    })


@user_passes_test(is_staff_user)
def create_election(request):
    """Create a new election"""
    if request.method == 'POST':
        form = ElectionForm(request.POST)
        if form.is_valid():
            election = form.save()
            messages.success(request, f'Election "{election.title}" created successfully!')
            return redirect('admin_dashboard')
    else:
        form = ElectionForm()
    
    return render(request, 'admin_panel/create_election.html', {'form': form})


@user_passes_test(is_staff_user)
def manage_candidates(request, election_id):
    """Manage candidates for a specific election"""
    election = get_object_or_404(Election, id=election_id)
    candidates = election.candidates.all()
    
    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES)
        if form.is_valid():
            candidate = form.save()
            messages.success(request, f'Candidate "{candidate.name}" added successfully!')
            return redirect('manage_candidates', election_id=election_id)
    else:
        form = CandidateForm(initial={'election': election})
    
    return render(request, 'admin_panel/manage_candidates.html', {
        'election': election,
        'candidates': candidates,
        'form': form,
    })


@user_passes_test(is_staff_user)
def delete_candidate(request, candidate_id):
    """Delete a candidate"""
    candidate = get_object_or_404(Candidate, id=candidate_id)
    election_id = candidate.election.id
    candidate.delete()
    messages.success(request, 'Candidate deleted successfully!')
    return redirect('manage_candidates', election_id=election_id)


@user_passes_test(is_staff_user)
def end_election(request, election_id):
    """Manually end an election and verify integrity"""
    election = get_object_or_404(Election, id=election_id)
    
    # Prevent ending already ended elections
    if election.has_ended():
        messages.warning(request, 'This election has already ended.')
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        # Validate hash chain before ending
        is_valid, error = validate_vote_chain(election)
        
        if not is_valid:
            messages.error(request, f'Cannot end election: Vote integrity check failed! {error}')
            return redirect('admin_dashboard')
        
        election.is_manually_ended = True
        election.save()
        messages.success(
            request, 
            f'✅ Election "{election.title}" has been ended. Integrity verified. Results are now available.'
        )
        return redirect('election_results', election_id=election_id)
    
    # GET request - show confirmation page
    return render(request, 'admin_panel/end_election_confirm.html', {
        'election': election,
    })
