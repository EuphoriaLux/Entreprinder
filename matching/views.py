from django.shortcuts import render, redirect
from django.urls import reverse
from entreprinder.models import EntrepreneurProfile, Like, Match
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import SwipeForm
from django.db.models import Q  # Add this import


@login_required
def swipe_action(request):
    if request.method == 'POST':
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
        
        # Fetch the next profile
        excluded_profiles = Like.objects.filter(liker=current_user).values_list('liked', flat=True)
        excluded_profiles = list(excluded_profiles) + [current_user.id]
        next_profile = EntrepreneurProfile.objects.exclude(id__in=excluded_profiles).first()
        
        response_data = {
            'status': 'match' if match_found else 'success',
        }

        if match_found:
            match_profile_picture = liked_profile.get_profile_picture_url()
            response_data['match_profile'] = {
                'id': liked_profile.id,
                'full_name': liked_profile.user.get_full_name() or liked_profile.user.username,
                'profile_picture': request.build_absolute_uri(match_profile_picture),
            }
        
        if next_profile:
            next_profile_picture = next_profile.get_profile_picture_url()
            response_data['next_profile'] = {
                'id': next_profile.id,
                'full_name': next_profile.user.get_full_name() or next_profile.user.username,
                'industry': next_profile.industry,
                'company': next_profile.company,
                'bio': next_profile.bio,
                'profile_picture': request.build_absolute_uri(next_profile_picture),
            }
        else:
            response_data['status'] = 'no_more_profiles'
            response_data['redirect_url'] = reverse('matching:no_more_profiles')
        
        return JsonResponse(response_data)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@login_required
def no_more_profiles(request):
    return render(request, 'matching/no_more_profiles.html')

@login_required
def matches(request):
    try:
        user_profile = EntrepreneurProfile.objects.get(user=request.user)
        matches = Match.objects.filter(Q(entrepreneur1=user_profile) | Q(entrepreneur2=user_profile))
        return render(request, 'matches.html', {'matches': matches})
    except Exception as e:
        return render(request, 'error.html', {'error_message': "An error occurred while loading your matches. Please try again later."})
    


@login_required
def swipe(request):
    current_user = request.user.entrepreneurprofile
    
    # Get profiles that haven't been interacted with
    interacted_profiles = Like.objects.filter(liker=current_user).values_list('liked', flat=True)
    profile_to_display = EntrepreneurProfile.objects.exclude(
        Q(user=request.user) | Q(id__in=interacted_profiles)
    ).first()

    if not profile_to_display:
        return render(request, 'matching/no_more_profiles.html')

    if request.method == 'POST':
        form = SwipeForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            entrepreneur_id = form.cleaned_data['entrepreneur_id']
            liked_profile = EntrepreneurProfile.objects.get(id=entrepreneur_id)
            
            if action == 'like':
                Like.objects.create(liker=current_user, liked=liked_profile)
            
            return redirect('entreprinder:swipe2')
    else:
        form = SwipeForm(initial={'entrepreneur_id': profile_to_display.id})

    context = {
        'form': form,
        'profile': profile_to_display,
    }
    return render(request, 'entreprinder/swipe2.html', context)