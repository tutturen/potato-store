from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib import messages
from products.forms import NotifyUserForm
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings


def notify_user(request, admin):
    if request.method == 'POST':
        form = NotifyUserForm(request.POST)
        if form.is_valid():
            num_sent = 0
            for user in form.cleaned_data['recipients']:
                if not user.email:
                    continue
                address = user.email
                subject = form.cleaned_data['subject']
                # TODO: Make replacements in body
                body = form.cleaned_data['body']
                num_sent += perform_user_notification(address, subject, body)
            message = '1 message was sent' if num_sent == 1 else\
                '%s messages were sent' % num_sent
            messages.success(request, message)
            # TODO: Redirect back to the page the user was on
            return HttpResponseRedirect('/admin/')
    else:
        user_id_field = request.GET.get('u', None)
        if user_id_field is not None:
            user_ids = user_id_field.split(',')
            user_ids = map(int, user_ids)
            users = User.objects.filter(pk__in=user_ids)

            # Did any users lack email info?
            users_with_email = users.filter(email__isnull=False)\
                .exclude(email='')
            num_users_wo_email = users.count() - users_with_email.count()
            if num_users_wo_email > 0:
                if num_users_wo_email == 1:
                    message = '1 user is missing email address.' \
                              ' They will be ignored.'
                else:
                    message = '%s users are missing their email address.' \
                              ' They will be ignored.' \
                        % num_users_wo_email
                messages.warning(request, message)

            # Set which users we want to select
            initial = {'recipients': users_with_email}
        else:
            # Select no users
            initial = None
        form = NotifyUserForm(initial=initial)

    context = dict(
        admin.each_context(request),
        form=form,
        title='Notify users',
    )

    return render(request, 'products/notify_user.html', context)


def perform_user_notification(address, subject, body):
    success = send_mail(
        subject,
        body,
        settings.EMAIL_FROM_ADDRESS,
        [address],
    )
    print('Send email to', address, 'with subject', subject, 'and body', body)
    return success
