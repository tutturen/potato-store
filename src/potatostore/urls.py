from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic import TemplateView

from graphene_django.views import GraphQLView

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^graphql', GraphQLView.as_view(graphiql=True)),
    url(r'^$', TemplateView.as_view(template_name='potatostore/index.html')),
]
