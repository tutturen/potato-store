import graphene
from graphene_django.types import DjangoObjectType
from products.models import Category, Product, User, PercentSale, PackageDeal
from django.db.models import Q
from functools import reduce

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

class CreateAccount(graphene.Mutation):
    class Arguments:
        firstName = graphene.String(required=True)
        lastName = graphene.String(required=True)
        username = graphene.String(required=True)

    result = graphene.Field(LoginResultType)

    def mutate(self, info, firstName, lastName, username):
        try:
            user = User.objects.create (
                firstName = firstName,
                lastName = lastName,
                username = username)
            user.save()
            result = LoginResultType(success=True, token="This is a token muhaha")
            return CreateAccount(result=result)
        except:
            print("Failed to create user")
            result = LoginResultType(success=False)
            return CreateAccount(result=result)

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

        # First phase of filtering is to check single-field
        #  values of the filter
        # text filter maps to name and subtitle, which
        #  can be checked relationally
        field_mappings = {
            'text': ['name', 'subtitle'],
            'minPrice': ['price'],
            'maxPrice': ['price'],
            'organic': ['organic']
        }

        # Create a kwargs object that can be filtered with,
        #  relational operators vary per field
        def search_fields(filterName, filterValue):
            if filterName not in field_mappings:
                return {}

            kw = {}
            for mapping in field_mappings[filterName]:
                # Generate the filter
                if filterName == 'text':
                    kw.update({mapping + '__contains': filterValue})
                elif filterName == 'minPrice':
                    kw.update({mapping + '__range': (filterValue, 1000)})
                elif filterName == 'maxPrice':
                    kw.update({mapping + '__range': (0, filterValue)})
                elif filterName == 'organic':
                    kw.update({mapping: filterValue})

            return kw

        # For text field, we must perform a union of
        #  name and subtitle results
        # For other fields, just perform intersection of results
        products = Product.objects.all()
        # filter_info = {}
        for field in filter:
            q = search_fields(field, filter[field])
            # If no filter was created, skip
            # Otherwise we get empty results
            if len(q) == 0:
                continue
            qset = None
            for constraint in q:
                if qset is None:
                    qset = products.filter(**{constraint: q[constraint]})
                else:
                    qset = qset | products.filter(**{constraint: q[constraint]})

            products = qset

        # Check whether product's category is queried
        # We need to do a union on this field, but intersection with previous results
        if 'category' in filter and products is not None:
            categories = filter['category']
            qset = None
            for cat in categories:
                kw = {'category': cat}
                if qset is None:
                    qset = products.filter(**kw)
                else:
                    qset = qset | products.filter(**kw)
            products = qset

        if 'onSale' in filter and filter['onSale']:
            products = products.filter(percentSale__isnull=False) | products.filter(packageDeal__isnull=False)

        # As a safety net, is products has become empty
        if products is None:
            products = []

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

class Mutation(graphene.ObjectType):
    create_account = CreateAccount.Field()
