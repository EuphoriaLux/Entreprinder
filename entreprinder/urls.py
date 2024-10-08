from django.urls import path
from . import views

app_name = 'entreprinder'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about_page, name='about'),
    path('contact/', views.contact_page, name='contact'),
    path('profile/', views.profile, name='profile'),
    path('entrepreneurs/', views.entrepreneur_list, name='entrepreneur_list'),
]