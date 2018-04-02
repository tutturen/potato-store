from django import forms
from products.models import User


class NotifyUserForm(forms.Form):
    recipients = forms.ModelMultipleChoiceField(
        User.objects.filter(email__isnull=False),
    )
    subject = forms.CharField(label='Email subject', max_length=150)
    body = forms.CharField(label='Email body', widget=forms.Textarea)
