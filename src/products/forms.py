from django import forms
from django.core.validators import MinLengthValidator
from django.contrib.auth.models import User


class NotifyUserForm(forms.Form):
    recipients = forms.ModelMultipleChoiceField(
        # Let admin pick any user which has a registered email address
        User.objects.filter(email__isnull=False).exclude(email=''),
        # Require that at least one user is picked
        validators=[MinLengthValidator(1)],
    )
    subject = forms.CharField(label='Email subject', max_length=150)
    body = forms.CharField(label='Email body', widget=forms.Textarea)
