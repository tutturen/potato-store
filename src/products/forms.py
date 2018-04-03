from django import forms
from django.core.validators import MinLengthValidator
from django.contrib.auth.models import User


class UserModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.get_full_name() + " (" + obj.username + ")"


class NotifyUserForm(forms.Form):
    recipients = UserModelMultipleChoiceField(
        # Let admin pick any user which has a registered email address
        User.objects.filter(email__isnull=False).exclude(email=''),
        # Require that at least one user is picked
        validators=[MinLengthValidator(1)],
        help_text="Hold down CTRL while clicking to select/deselect multiple "
                  "users."
    )
    subject = forms.CharField(label='Email subject', max_length=150)
    body = forms.CharField(label='Email body', widget=forms.Textarea)
