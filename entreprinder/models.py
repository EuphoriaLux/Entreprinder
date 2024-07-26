from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class EntrepreneurProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    company = models.CharField(max_length=100, blank=True)
    industry = models.CharField(max_length=100)
    looking_for = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.username}'s profile"

    def get_profile_picture_url(self):
        if self.profile_picture and self.profile_picture.name:
            return self.profile_picture.url
        return f"{settings.STATIC_URL}images/default-profile.png"

class Skill(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class EntrepreneurSkill(models.Model):
    entrepreneur = models.ForeignKey(EntrepreneurProfile, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('entrepreneur', 'skill')

class Match(models.Model):
    entrepreneur1 = models.ForeignKey(EntrepreneurProfile, on_delete=models.CASCADE, related_name='matches_as_first')
    entrepreneur2 = models.ForeignKey(EntrepreneurProfile, on_delete=models.CASCADE, related_name='matches_as_second')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('entrepreneur1', 'entrepreneur2')

class Like(models.Model):
    liker = models.ForeignKey(EntrepreneurProfile, on_delete=models.CASCADE, related_name='likes_given')
    liked = models.ForeignKey(EntrepreneurProfile, on_delete=models.CASCADE, related_name='likes_received')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('liker', 'liked')