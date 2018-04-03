from django import forms
from django.core.validators import MinLengthValidator
from django.contrib.auth.models import User


class NotifyUserForm(forms.Form):
    recipients = forms.ModelMultipleChoiceField(
        User.objects.filter(email__isnull=False),
        validators=[MinLengthValidator(1)],
    )
    subject = forms.CharField(label='Email subject', max_length=150)
    body = forms.CharField(label='Email body', widget=forms.Textarea)
