from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib import messages
from products.forms import NotifyUserForm


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
                perform_user_notification(address, subject, body)
                num_sent += 1
            message = '1 message was sent' if num_sent == 1 else\
                '%s messages were sent' % num_sent
            messages.success(request, message)
            # TODO: Redirect back to the page the user was on
            return HttpResponseRedirect('/admin/')
    else:
        # TODO: Prefill list of users from GET fields (set by admin action)
        form = NotifyUserForm()

    context = dict(
        admin.each_context(request),
        form=form,
        title='Notify users',
    )

    return render(request, 'products/notify_user.html', context)


def perform_user_notification(address, subject, body):
    # TODO: Implement the actual sending of emails
    print('Send email to', address, 'with subject', subject, 'and body', body)
