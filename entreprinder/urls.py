from django.urls import path
from . import views
from .views import RedisCacheTestView  # Make sure to import the view

app_name = 'entreprinder'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about_page, name='about'),
    path('contact/', views.contact_page, name='contact'),
    path('profile/', views.profile, name='profile'),
    path('entrepreneurs/', views.entrepreneur_list, name='entrepreneur_list'),
    path('swipe/', views.swipe, name='swipe'),
    path('swipe-action/', views.swipe_action, name='swipe_action'),
    path('matches/', views.matches, name='matches'),
    path('no-more-profiles/', views.no_more_profiles, name='no_more_profiles'),
    path('test-redis/', RedisCacheTestView.as_view(), name='test-redis'),
]