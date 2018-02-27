import graphene
from graphene_django.types import DjangoObjectType
from products.models import Category, Product, User


class CategoryType(DjangoObjectType):
    class Meta:
        model = Category


class ProductType(DjangoObjectType):
    class Meta:
        model = Product

class UserType(DjangoObjectType):
    class Meta:
        model = User

class Query(object):
    all_categories = graphene.List(CategoryType)
    all_products = graphene.List(ProductType)
    all_users = graphene.List(UserType)

    def resolve_all_categories(self, info, **kwargs):
        return Category.objects.all()

    def resolve_all_products(self, info, **kwargs):
        # We can easily optimize query count in the resolve method
        return Product.objects.select_related('category').all()

    def resolve_all_users(self, info, **kwargs):
        return User.objects.all()
