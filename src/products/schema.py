import graphene
from graphene_django.types import DjangoObjectType
from products.models import Category, Product, User, PercentSale, PackageDeal
from django.db.models.query import QuerySet


class CategoryType(DjangoObjectType):
    class Meta:
        model = Category


class ProductType(DjangoObjectType):
    class Meta:
        model = Product


class UserType(DjangoObjectType):
    class Meta:
        model = User


class PercentSaleType(DjangoObjectType):
    class Meta:
        model = PercentSale


class PackageDealType(DjangoObjectType):
    class Meta:
        model = PackageDeal


class CartType(graphene.ObjectType):
    products = graphene.List(lambda: ProductType)
    totalBeforeDiscount = graphene.Float()
    totalDiscount = graphene.Float()
    total = graphene.Float()


class LoginResultType(graphene.ObjectType):
    user = UserType
    success = graphene.Boolean()
    token = graphene.String()


class FilterInputType(graphene.InputObjectType):
    text = graphene.String(required=False)
    minPrice = graphene.Float(required=False)
    maxPrice = graphene.Float(required=False)
    category = graphene.List(graphene.ID, required=False)
    onSale = graphene.Boolean(required=False)
    organic = graphene.Boolean(required=False)


class Query(graphene.ObjectType):
    all_categories = graphene.NonNull(graphene.List(graphene.NonNull(CategoryType)))
    all_products = graphene.Field(
        type=graphene.NonNull(graphene.List(graphene.NonNull(ProductType))),
        filter=graphene.Argument(FilterInputType)
    )
    category = graphene.Field(CategoryType,
                              categoryName=graphene.String())
    cart = graphene.Field(CartType,
                          products=graphene.NonNull(graphene.List(graphene.ID)))

    def resolve_all_categories(self, info):
        return Category.objects.all()

    def resolve_all_products(self, info, filter={}):

        field_mappings = {
            'text': ['name', 'subtitle'],
            'minPrice': ['price'],
            'maxPrice': ['price']
        }

        def search_fields(products, filterName, filterValue):
            if filterName not in field_mappings:
                return products

            new_products = None
            for mapping in field_mappings[filterName]:
                kw = None
                # Generate the filter
                if filterName == 'text':
                    kw = {mapping + '__contains': filterValue}
                elif filterName == 'minPrice':
                    kw = {'price__gte': filterValue}
                elif filterName == 'maxPrice':
                    kw = {'price__lte': filterValue}

                # Do the filtering and union
                print(kw)
                if new_products is not None:
                    new_products = new_products.union(products.filter(**kw))
                else:
                    new_products = products.filter(**kw)

            return new_products

        # We can easily optimize query count in the resolve method
        products = Product.objects.all()
        for field in filter:
            products = search_fields(products, field, filter[field])

        print(type(products), len(products))
        return products

    def resolve_category(self, info, **kwargs):
        try:
            return Category.objects.filter(name=kwargs['categoryName'])[0]
        except IndexError:
            return None

    def resolve_cart(self, info, **kwargs):
        # Product IDs requested and results to return
        products = kwargs['products']
        dbproducts = []

        # Create empty cart type
        cart = CartType(totalBeforeDiscount=0,
                        totalDiscount=0,
                        total=0)

        # For every product requested
        for productId in products:
            # Query the database
            query = Product.objects.filter(id=productId)

            # Add all to the result list
            dbproducts = dbproducts + [x for x in query]

            # Calculate prices if possible
            if len(query) != 0:
                # Add item price
                cart.totalBeforeDiscount += query[0].price

                # Default no sale
                saleprice = query[0].price

                # If there are discounts
                if query[0].percentSale:
                    saleprice = query[0].price * query[0].percentSale.cut * 0.01
                if query[0].packageDeal:
                    # We need to count stuff then divide by minimum quantity
                    # to figure out how many times to apply the paid quantity.
                    pass

                # At last add sum
                cart.totalDiscount += query[0].price - saleprice
                cart.total += saleprice

        # Return cart with products
        cart.products = dbproducts
        return cart
