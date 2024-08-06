from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Button, Div
from django import forms

# Create your views here.
class SwipeForm(forms.Form):
    entrepreneur_id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'swipe-form'
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'entrepreneur_id',
            Div(
                Button('pass', '👎 Pass', css_class='btn btn-danger mr-2', onclick='submitForm("pass")'),
                Button('like', '👍 Like', css_class='btn btn-success', onclick='submitForm("like")'),
                css_class='d-flex justify-content-between mt-3'
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        action = self.data.get('action')
        if action not in ['pass', 'like']:
            raise forms.ValidationError("Invalid action")
        cleaned_data['action'] = action
        return cleaned_data