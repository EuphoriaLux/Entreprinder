from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import EntrepreneurProfile, Like, Match
from .forms import EntrepreneurProfileForm
import json

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
    current_user_profile = EntrepreneurProfile.objects.get(user=request.user)
    liked_profiles = Like.objects.filter(liker=current_user_profile).values_list('liked_id', flat=True)
    profiles = EntrepreneurProfile.objects.exclude(user=request.user).exclude(id__in=liked_profiles)
    return render(request, 'entrepreneur_list.html', {'profiles': profiles})

@login_required
def swipe(request):
    current_user = request.user.entrepreneurprofile
    excluded_profiles = Like.objects.filter(liker=current_user).values_list('liked', flat=True)
    excluded_profiles = list(excluded_profiles) + [current_user.id]
    
    profiles_to_swipe = EntrepreneurProfile.objects.exclude(id__in=excluded_profiles)
    
    context = {
        'profiles': profiles_to_swipe,
        'debug_info': 'This is a debug message',
    }
    return render(request, 'entreprinder/swipe.html', context)

@login_required
@require_POST
def swipe_action(request):
    data = json.loads(request.body)
    profile_id = data.get('profile_id')
    action = data.get('action')
    
    liked_profile = get_object_or_404(EntrepreneurProfile, id=profile_id)
    current_user = request.user.entrepreneurprofile
    
    if action == 'like':
        like, created = Like.objects.get_or_create(liker=current_user, liked=liked_profile)
        
        # Check if it's a match
        if Like.objects.filter(liker=liked_profile, liked=current_user).exists():
            Match.objects.get_or_create(entrepreneur1=current_user, entrepreneur2=liked_profile)
            return JsonResponse({'status': 'match', 'profile_id': profile_id})
        
        return JsonResponse({'status': 'liked', 'profile_id': profile_id})
    elif action == 'dislike':
        # You might want to store dislikes as well, or just pass
        pass
    
    return JsonResponse({'status': 'success', 'profile_id': profile_id})

@login_required
def matches(request):
    user_profile = EntrepreneurProfile.objects.get(user=request.user)
    matches = Match.objects.filter(Q(entrepreneur1=user_profile) | Q(entrepreneur2=user_profile))
    return render(request, 'matches.html', {'matches': matches})