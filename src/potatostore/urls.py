from django.conf.urls import url, include
from products.admin import our_admin
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.views.generic import TemplateView

from graphene_django.views import GraphQLView

urlpatterns = [
    url(r'^admin/', our_admin.urls),
    url(r'^graphql', csrf_exempt(GraphQLView.as_view(graphiql=True))),
    url(r'^$', ensure_csrf_cookie(
        TemplateView.as_view(template_name='potatostore/index.html')
    )),
]
