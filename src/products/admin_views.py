from django.shortcuts import render
from django.http import HttpResponseRedirect
from products.forms import NotifyUserForm


def notify_user(request):
    if request.method == 'POST':
        form = NotifyUserForm(request.POST)
        # TODO: Check that at least one user was picked as recipient
        if form.is_valid():
            for user in form.cleaned_data['recipients']:
                if not user.email:
                    continue
                address = user.email
                subject = form.cleaned_data['subject']
                # TODO: Make replacements in body
                body = form.cleaned_data['body']
                perform_user_notification(address, subject, body)
            # TODO: Redirect with success message
            # TODO: Redirect back to the page the user was on
            return HttpResponseRedirect('/admin/')
    else:
        # TODO: Prefill list of users from GET fields (set by admin action)
        form = NotifyUserForm()

    return render(request, 'notify_user.html', {
                      'form': form,
                      'title': 'Notify users',
                  })


def perform_user_notification(address, subject, body):
    # TODO: Implement the actual sending of emails
    print('Send email to', address, 'with subject', subject, 'and body', body)
