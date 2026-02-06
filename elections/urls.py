from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),

    # ============= OTP Authentication (Replaces Django Auth) =============
    path('auth/request-otp/', views.request_otp, name='request_otp'),
    path('auth/verify-otp/', views.verify_otp, name='verify_otp'),
    path('auth/logout/', views.logout_view, name='logout'),
    
    # Legacy Django admin login (for staff only)
    path('admin-login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='admin_login'),
    
    # Voter views (OTP session required)
    path('dashboard/', views.voter_dashboard, name='voter_dashboard'),
    path('election/<int:election_id>/candidates/', views.candidate_list, name='candidate_list'),
    path('election/<int:election_id>/vote/', views.cast_vote, name='cast_vote'),
    path('election/<int:election_id>/results/', views.election_results, name='election_results'),
    
    # Admin views (Django User auth required)
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/create-election/', views.create_election, name='create_election'),
    path('admin-panel/election/<int:election_id>/candidates/', views.manage_candidates, name='manage_candidates'),
    path('admin-panel/candidate/<int:candidate_id>/delete/', views.delete_candidate, name='delete_candidate'),
    path('admin-panel/election/<int:election_id>/end/', views.end_election, name='end_election'),
]
