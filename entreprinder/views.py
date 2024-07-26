from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import EntrepreneurProfile, Like, Match
from .forms import EntrepreneurProfileForm
import json
import logging

logger = logging.getLogger(__name__)

def home(request):
    return render(request, 'landing_page.html')

def about_page(request):
    return render(request, 'about.html')

def contact_page(request):
    return render(request, 'contact.html')

@login_required
def profile(request):
    try:
        profile = EntrepreneurProfile.objects.get(user=request.user)
    except EntrepreneurProfile.DoesNotExist:
        profile = EntrepreneurProfile(user=request.user)

    if request.method == 'POST':
        form = EntrepreneurProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('entreprinder:profile')
    else:
        form = EntrepreneurProfileForm(instance=profile)
    return render(request, 'profile.html', {'form': form})

@login_required
def entrepreneur_list(request):
    try:
        current_user_profile, created = EntrepreneurProfile.objects.get_or_create(user=request.user)
        if created:
            logger.info(f"New EntrepreneurProfile created for user {request.user.username}")
            return redirect('entreprinder:profile')
        
        liked_profiles = Like.objects.filter(liker=current_user_profile).values_list('liked_id', flat=True)
        profiles = EntrepreneurProfile.objects.exclude(user=request.user).exclude(id__in=liked_profiles)
        
        logger.info(f"Entrepreneur list loaded for user {request.user.username}. {profiles.count()} profiles found.")
        
        return render(request, 'entrepreneur_list.html', {'profiles': profiles})
    except Exception as e:
        logger.error(f"An error occurred in entrepreneur_list view for user {request.user.username}: {str(e)}")
        return render(request, 'error.html', {'error_message': "An error occurred while loading the entrepreneur list. Please try again later."})


@login_required
def swipe(request):
    try:
        current_user = request.user.entrepreneurprofile
        excluded_profiles = Like.objects.filter(liker=current_user).values_list('liked', flat=True)
        excluded_profiles = list(excluded_profiles) + [current_user.id]
        
        profile_to_swipe = EntrepreneurProfile.objects.exclude(id__in=excluded_profiles).first()
        
        context = {
            'profile': profile_to_swipe,
            'debug_info': 'This is a debug message',
        }
        return render(request, 'entreprinder/swipe.html', context)
    except Exception as e:
        logger.error(f"An error occurred in swipe view: {str(e)}")
        return render(request, 'error.html', {'error_message': "An error occurred while loading a profile to swipe. Please try again later."})

@login_required
@require_POST
def swipe_action(request):
    try:
        data = json.loads(request.body)
        profile_id = data.get('profile_id')
        action = data.get('action')
        
        liked_profile = get_object_or_404(EntrepreneurProfile, id=profile_id)
        current_user = request.user.entrepreneurprofile
        
        match_found = False
        if action == 'like':
            like, created = Like.objects.get_or_create(liker=current_user, liked=liked_profile)
            
            # Check if it's a match
            if Like.objects.filter(liker=liked_profile, liked=current_user).exists():
                Match.objects.get_or_create(entrepreneur1=current_user, entrepreneur2=liked_profile)
                match_found = True
        elif action == 'dislike':
            # You might want to store dislikes as well, or just pass
            pass
        
        # Fetch the next profile
        excluded_profiles = Like.objects.filter(liker=current_user).values_list('liked', flat=True)
        excluded_profiles = list(excluded_profiles) + [current_user.id]
        next_profile = EntrepreneurProfile.objects.exclude(id__in=excluded_profiles).first()
        
        response_data = {
            'status': 'match' if match_found else 'success',
            'next_profile': None
        }

        if next_profile:
            response_data['next_profile'] = {
                'id': next_profile.id,
                'full_name': next_profile.user.get_full_name(),
                'industry': next_profile.industry,
                'company': next_profile.company,
                'bio': next_profile.bio,
                'profile_picture': next_profile.profile_picture.url if next_profile.profile_picture else None,
            }

        if match_found:
            response_data['match_profile'] = {
                'id': liked_profile.id,
                'full_name': liked_profile.user.get_full_name(),
                'profile_picture': liked_profile.profile_picture.url if liked_profile.profile_picture else None,
            }

        return JsonResponse(response_data)
    except json.JSONDecodeError:
        logger.error("Invalid JSON data received in swipe_action")
        return JsonResponse({'status': 'error', 'message': 'Invalid data received'}, status=400)
    except Exception as e:
        logger.error(f"An error occurred in swipe_action view: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'An unexpected error occurred'}, status=500)

@login_required
def matches(request):
    try:
        user_profile = EntrepreneurProfile.objects.get(user=request.user)
        matches = Match.objects.filter(Q(entrepreneur1=user_profile) | Q(entrepreneur2=user_profile))
        return render(request, 'matches.html', {'matches': matches})
    except Exception as e:
        logger.error(f"An error occurred in matches view: {str(e)}")
        return render(request, 'error.html', {'error_message': "An error occurred while loading your matches. Please try again later."})