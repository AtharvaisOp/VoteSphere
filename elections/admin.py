from django.contrib import admin
from django.utils.html import format_html, mark_safe
from .models import Election, Candidate


class CandidateInline(admin.TabularInline):
    """Inline admin for managing candidates within an election"""
    model = Candidate
    extra = 1
    fields = ['name', 'position', 'description', 'photo']


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    """Admin interface for Election model"""
    list_display = ['title', 'start_date', 'end_date', 'is_active', 'status_badge', 'candidate_count', 'locked_status']
    list_filter = ['is_active', 'start_date', 'end_date']
    search_fields = ['title', 'description']
    date_hierarchy = 'start_date'
    inlines = [CandidateInline]
    
    fieldsets = (
        ('Election Information', {
            'fields': ('title', 'description')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date', 'is_active')
        }),
    )
    
    def status_badge(self, obj):
        """Display election status with color coding"""
        if obj.is_ongoing():
            return mark_safe('<span style="color: green; font-weight: bold;">● ONGOING</span>')
        elif obj.has_ended():
            return mark_safe('<span style="color: red;">● ENDED</span>')
        else:
            return mark_safe('<span style="color: orange;">● UPCOMING</span>')
    status_badge.short_description = 'Status'
    
    def candidate_count(self, obj):
        """Display number of candidates"""
        return obj.candidates.count()
    candidate_count.short_description = 'Candidates'
    
    def locked_status(self, obj):
        """Display lock icon if election cannot be edited"""
        if obj.has_ended():
            return mark_safe('🔒 <span style="color: #999;">Locked</span>')
        elif obj.is_ongoing():
            return mark_safe('🔓 <span style="color: orange;">Restricted</span>')
        return mark_safe('✏️ <span style="color: green;">Editable</span>')
    locked_status.short_description = 'Editing'
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of elections that have started or ended"""
        if obj and (obj.is_ongoing() or obj.has_ended()):
            return False
        return super().has_delete_permission(request, obj)
    
    def has_change_permission(self, request, obj=None):
        """Prevent editing of elections that have ended"""
        if obj and obj.has_ended():
            return False
        return super().has_change_permission(request, obj)
    
    def get_readonly_fields(self, request, obj=None):
        """Make critical fields read-only for ongoing elections"""
        if obj and obj.is_ongoing():
            # Can't change dates or title for ongoing elections
            return ['title', 'start_date', 'end_date']
        return []


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    """Admin interface for Candidate model"""
    list_display = ['name', 'position', 'election', 'vote_count', 'photo_preview', 'locked_status']
    list_filter = ['position', 'election']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Candidate Information', {
            'fields': ('election', 'name', 'position')
        }),
        ('Details', {
            'fields': ('description', 'photo')
        }),
    )
    
    def vote_count(self, obj):
        """Display vote count for this candidate"""
        return obj.get_vote_count()
    vote_count.short_description = 'Votes'
   
    def photo_preview(self, obj):
        """Display thumbnail of candidate photo"""
        if obj.photo:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%;" />', obj.photo.url)
        return '-'
    photo_preview.short_description = 'Photo'
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of candidates if election has started or ended"""
        if obj and obj.election and (obj.election.is_ongoing() or obj.election.has_ended()):
            return False
        return super().has_delete_permission(request, obj)
    
    def has_change_permission(self, request, obj=None):
        """Prevent editing of candidates if election has ended"""
        if obj and obj.election and obj.election.has_ended():
            return False
        return super().has_change_permission(request, obj)
    
    def get_readonly_fields(self, request, obj=None):
        """Make all fields read-only for ongoing elections"""
        if obj and obj.election and obj.election.is_ongoing():
            return ['election', 'name', 'position', 'description', 'photo']
        return []
    
    def locked_status(self, obj):
        """Display lock icon if candidate cannot be edited"""
        if obj.election.has_ended():
            return mark_safe('🔒 <span style="color: #999;">Locked</span>')
        elif obj.election.is_ongoing():
            return mark_safe('🔓 <span style="color: orange;">Restricted</span>')
        return mark_safe('✏️ <span style="color: green;">Editable</span>')
    locked_status.short_description = 'Editing'


# ============= SECURITY: Vote Model NOT Registered =============
# The Vote model is intentionally NOT registered in admin to prevent tampering.
# Votes are encrypted and protected by hash chain integrity.
# No admin interface is provided for viewing or modifying votes.
