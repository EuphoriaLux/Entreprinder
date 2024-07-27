from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import EntrepreneurProfile, Like, Match
from .forms import EntrepreneurProfileForm
import json
from django.core.cache import cache
from django.urls import reverse
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib import messages
from django.http import HttpResponse
from django.views import View


class RedisCacheTestView(View):
    def get(self, request):
        try:
            # Try to set a value in the cache
            cache.set('test_key', 'test_value', timeout=30)
            
            # Try to retrieve the value from the cache
            cached_value = cache.get('test_key')
            
            if cached_value == 'test_value':
                return HttpResponse("Redis cache is working correctly!")
            else:
                return HttpResponse("Redis cache test failed: Value not retrieved correctly.")
        except Exception as e:
            return HttpResponse(f"Redis cache test failed with error: {str(e)}")

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
            profile = form.save(commit=False)
            if 'profile_picture' in request.FILES:
                profile.profile_picture = request.FILES['profile_picture']
            profile.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('entreprinder:profile')
        else:
            messages.error(request, 'Error updating profile. Please check the form.')
    else:
        form = EntrepreneurProfileForm(instance=profile)

    return render(request, 'profile.html', {'form': form})

@login_required
def entrepreneur_list(request):
    try:
        current_user_profile, created = EntrepreneurProfile.objects.get_or_create(user=request.user)
        if created:
            return redirect('entreprinder:profile')
        
        liked_profiles = Like.objects.filter(liker=current_user_profile).values_list('liked_id', flat=True)
        profiles = EntrepreneurProfile.objects.exclude(user=request.user).exclude(id__in=liked_profiles)

        
        return render(request, 'entrepreneur_list.html', {'profiles': profiles})
    except Exception as e:
        return render(request, 'error.html', {'error_message': "An error occurred while loading the entrepreneur list. Please try again later."})

@login_required
def swipe(request):
    current_user = request.user.entrepreneurprofile
    excluded_profiles = Like.objects.filter(liker=current_user).values_list('liked', flat=True)
    excluded_profiles = list(excluded_profiles) + [current_user.id]
    
    profile_to_swipe = EntrepreneurProfile.objects.exclude(id__in=excluded_profiles).first()
    
    if profile_to_swipe:
        profile_data = {
            'id': profile_to_swipe.id,
            'full_name': profile_to_swipe.user.get_full_name() or profile_to_swipe.user.username,
            'industry': profile_to_swipe.industry,
            'company': profile_to_swipe.company,
            'bio': profile_to_swipe.bio,
            'profile_picture': request.build_absolute_uri(profile_to_swipe.get_profile_picture_url()),
        }
        context = {
            'profile': json.dumps(profile_data),
            'current_user_picture': request.build_absolute_uri(current_user.get_profile_picture_url())
        }
        return render(request, 'entreprinder/swipe.html', context)
    else:
        return redirect(reverse('entreprinder:no_more_profiles'))

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
            response_data['redirect_url'] = reverse('entreprinder:no_more_profiles')
        
        return JsonResponse(response_data)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@login_required
def no_more_profiles(request):
    return render(request, 'entreprinder/no_more_profiles.html')

@login_required
def matches(request):
    try:
        user_profile = EntrepreneurProfile.objects.get(user=request.user)
        matches = Match.objects.filter(Q(entrepreneur1=user_profile) | Q(entrepreneur2=user_profile))
        return render(request, 'matches.html', {'matches': matches})
    except Exception as e:
        return render(request, 'error.html', {'error_message': "An error occurred while loading your matches. Please try again later."})
    
