
from django.contrib import admin
from .models import EntrepreneurProfile, Skill, EntrepreneurSkill, Match, Like

@admin.register(EntrepreneurProfile)
class EntrepreneurProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'industry', 'location')
    search_fields = ('user__username', 'company', 'industry', 'location')
    list_filter = ('industry', 'location')

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(EntrepreneurSkill)
class EntrepreneurSkillAdmin(admin.ModelAdmin):
    list_display = ('entrepreneur', 'skill')
    list_filter = ('skill',)
    search_fields = ('entrepreneur__user__username', 'skill__name')

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('entrepreneur1', 'entrepreneur2', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('entrepreneur1__user__username', 'entrepreneur2__user__username')

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('liker', 'liked', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('liker__user__username', 'liked__user__username')