from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

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

@receiver(post_save, sender=Like)
def create_match(sender, instance, created, **kwargs):
    if created:
        # Check if there's a mutual like
        mutual_like = Like.objects.filter(liker=instance.liked, liked=instance.liker).exists()
        if mutual_like:
            # Create a match
            Match.objects.get_or_create(
                entrepreneur1=instance.liker,
                entrepreneur2=instance.liked
            )