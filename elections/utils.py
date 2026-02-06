import io
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from collections import defaultdict
from .models import Candidate, Vote


def generate_election_results_chart(election, save_path):
    """
    Generate bar charts showing vote distribution for each position.
    Returns the path to the saved chart.
    """
    # Import decrypt_vote here to avoid circular imports
    from .crypto_utils import decrypt_vote
    
    # Group candidates by position
    positions = defaultdict(list)
    for candidate in election.candidates.all():
        positions[candidate.position].append(candidate)
    
    # Calculate number of subplots needed
    num_positions = len(positions)
    if num_positions == 0:
        return None
    
    # Decrypt votes and count
    vote_counts = defaultdict(lambda: defaultdict(int))
    for vote in election.votes.all():
        try:
            vote_data = decrypt_vote(vote.encrypted_vote)
            for position, candidate_id in vote_data.items():
                vote_counts[position][int(candidate_id)] += 1
        except Exception:
            pass
    
    # Create figure with subplots
    fig, axes = plt.subplots(num_positions, 1, figsize=(10, 5 * num_positions))
    if num_positions == 1:
        axes = [axes]
    
    # Generate a chart for each position
    for idx, (position, candidates) in enumerate(sorted(positions.items())):
        names = [c.name for c in candidates]
        votes = [vote_counts[position].get(c.id, 0) for c in candidates]
        
        # Create bar chart
        ax = axes[idx]
        bars = ax.bar(names, votes, color='#4A90E2', edgecolor='#2E5C8A', linewidth=1.5)
        
        # Customize chart
        position_label = dict(Candidate.POSITION_CHOICES).get(position, position)
        ax.set_title(f'{position_label} - Vote Distribution', fontsize=14, fontweight='bold')
        ax.set_xlabel('Candidates', fontsize=12)
        ax.set_ylabel('Number of Votes', fontsize=12)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom', fontweight='bold')
        
        # Rotate x-axis labels if needed
        if len(names) > 3:
            ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return save_path


def generate_pie_chart(election, save_path):
    """
    Generate pie charts showing vote percentage for each position.
    """
    # Import decrypt_vote here to avoid circular imports
    from .crypto_utils import decrypt_vote
    
    # Group candidates by position
    positions = defaultdict(list)
    for candidate in election.candidates.all():
        positions[candidate.position].append(candidate)
    
    num_positions = len(positions)
    if num_positions == 0:
        return None
    
    # Decrypt votes and count
    vote_counts = defaultdict(lambda: defaultdict(int))
    for vote in election.votes.all():
        try:
            vote_data = decrypt_vote(vote.encrypted_vote)
            for position, candidate_id in vote_data.items():
                vote_counts[position][int(candidate_id)] += 1
        except Exception:
            pass
    
    # Create figure with subplots
    cols = 2
    rows = (num_positions + 1) // 2
    fig, axes = plt.subplots(rows, cols, figsize=(12, 5 * rows))
    
    # Flatten axes array for easy iteration, handling the case where subplots returns a single object vs array
    if hasattr(axes, 'flatten'):
        axes = axes.flatten()
    elif not isinstance(axes, (list, getattr(matplotlib, 'artist', list))): 
        # Fallback if it returns a single axes object (though unlikely with cols=2)
        axes = [axes]
    
    # Generate a pie chart for each position
    for idx, (position, candidates) in enumerate(sorted(positions.items())):
        names = [c.name for c in candidates]
        votes = [vote_counts[position].get(c.id, 0) for c in candidates]
        
        # Only show pie chart if there are votes
        if sum(votes) > 0:
            ax = axes[idx]
            colors = plt.cm.Set3(range(len(names)))
            wedges, texts, autotexts = ax.pie(
                votes, 
                labels=names, 
                autopct='%1.1f%%',
                colors=colors,
                startangle=90
            )
            
            # Customize text
            for text in texts:
                text.set_fontsize(10)
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(9)
            
            position_label = dict(Candidate.POSITION_CHOICES).get(position, position)
            ax.set_title(f'{position_label}', fontsize=12, fontweight='bold')
    
    # Hide unused subplots
    for idx in range(num_positions, len(axes)):
        axes[idx].axis('off')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return save_path


def get_election_statistics(election):
    """
    Calculate and return statistics for an election.
    Uses decryption for secure vote counting.
    """
    from .crypto_utils import decrypt_vote
    
    total_votes = Vote.objects.filter(election=election).count()
    total_candidates = election.candidates.count()
    
    # Count unique voters (unique voter_hash values)
    unique_voters = Vote.objects.filter(election=election).values('voter_hash').distinct().count()
    
    # Decrypt and count votes for winners
    vote_counts = defaultdict(lambda: defaultdict(int))
    for vote in election.votes.all():
        try:
            vote_data = decrypt_vote(vote.encrypted_vote)
            for position, candidate_id in vote_data.items():
                vote_counts[position][int(candidate_id)] += 1
        except Exception:
            pass
    
    # Calculate winner for each position
    positions = defaultdict(list)
    for candidate in election.candidates.all():
        positions[candidate.position].append(candidate)
    
    winners = {}
    for position, candidates in positions.items():
        if candidates:
            # Find candidate with most votes
            max_votes = 0
            winner = None
            for candidate in candidates:
                votes = vote_counts[position].get(candidate.id, 0)
                if votes > max_votes:
                    max_votes = votes
                    winner = candidate
            
            if winner:
                winners[position] = {
                    'candidate': winner,
                    'votes': max_votes
                }
    
    return {
        'total_votes': total_votes,
        'total_candidates': total_candidates,
        'unique_voters': unique_voters,
        'winners': winners,
    }
