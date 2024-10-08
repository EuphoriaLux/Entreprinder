from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

class Industry(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Skill(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class EntrepreneurProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    tagline = models.CharField(max_length=150, blank=True, help_text="A brief, catchy description of yourself")
    company = models.CharField(max_length=100, blank=True)
    industry = models.ForeignKey(Industry, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.CharField(max_length=100, blank=True)
    skills = models.ManyToManyField(Skill, related_name='entrepreneurs')
    looking_for = models.TextField(max_length=500, blank=True)
    offering = models.TextField(max_length=500, blank=True, help_text="What can you offer to other entrepreneurs?")
    website = models.URLField(blank=True)
    linkedin_profile = models.URLField(blank=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    is_mentor = models.BooleanField(default=False)
    is_looking_for_funding = models.BooleanField(default=False)
    is_investor = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s profile"

    def get_profile_picture_url(self):
        if self.profile_picture and self.profile_picture.name:
            return self.profile_picture.url
        return f"{settings.STATIC_URL}images/default-profile.png"