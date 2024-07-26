from django import forms
from .models import EntrepreneurProfile

class EntrepreneurProfileForm(forms.ModelForm):
    class Meta:
        model = EntrepreneurProfile
        fields = ['profile_picture', 'bio', 'company', 'industry', 'looking_for', 'location']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'industry': forms.TextInput(attrs={'class': 'form-control'}),
            'looking_for': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profile_picture'].widget.attrs.update({'class': 'form-control-file'})