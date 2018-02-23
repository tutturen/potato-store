import graphene
from graphene_django.types import DjangoObjectType
from products.models import Category, Product


class CategoryType(DjangoObjectType):
    class Meta:
        model = Category


class ProductType(DjangoObjectType):
    class Meta:
        model = Product


class Query(object):
    all_categories = graphene.List(CategoryType)
    all_products = graphene.List(ProductType)

    def resolve_all_categories(self, info, **kwargs):
        return Category.objects.all()

    def resolve_all_products(self, info, **kwargs):
        # We can easily optimize query count in the resolve method
        return Product.objects.select_related('category').all()
