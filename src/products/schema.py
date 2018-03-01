import graphene
from graphene_django.types import DjangoObjectType
from products.models import Category, Product, User, Cart


class CategoryType(DjangoObjectType):
    class Meta:
        model = Category


class ProductType(DjangoObjectType):
    class Meta:
        model = Product


class UserType(DjangoObjectType):
    class Meta:
        model = User


class CartType(DjangoObjectType):
    class Meta:
        model = Cart


class Query(graphene.ObjectType):
    all_categories = graphene.NonNull(graphene.List(graphene.NonNull(CategoryType)))
    all_products = graphene.NonNull(graphene.List(graphene.NonNull(ProductType)))
    category = graphene.Field(CategoryType,
                              categoryName=graphene.String())
    cart = graphene.Field(CartType,
                          products=graphene.NonNull(graphene.List(graphene.ID)))

    def resolve_all_categories(self, info):
        return Category.objects.all()

    def resolve_all_products(self, info):
        # We can easily optimize query count in the resolve method
        return Product.objects.select_related('category').all()

    def resolve_category(self, info, **kwargs):
        try:
            return Category.objects.filter(name=kwargs['categoryName'])[0]
        except IndexError:
            return None

    def resolve_cart(self, info, **kwargs):
        products = kwargs['products']
        dbproducts = []

        cart = Cart(totalBeforeDiscount=0,
                    totalDiscount=0,
                    total=0)

        for productId in products:
            query = Product.objects.filter(id=productId)
            dbproducts = dbproducts + [x for x in query]
            if len(query) != 0:
                cart.totalBeforeDiscount += query[0].price

        return cart
