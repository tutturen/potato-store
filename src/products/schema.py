import graphene
import graphql_jwt
import django
from graphene_django.types import DjangoObjectType
from products.models import Category, Product, PercentSale, PackageDeal, Order

class CategoryType(DjangoObjectType):
    class Meta:
        model = Category

class ProductType(DjangoObjectType):
    class Meta:
        model = Product

class UserType(DjangoObjectType):
    class Meta:
        model = django.contrib.auth.models.User

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

    def processcart(products):
        # Product IDs requested and results to return
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

class LoginResultType(graphene.ObjectType):
    user = graphene.Field(UserType)
    success = graphene.Boolean()
    token = graphene.String()

class ReceiptType(graphene.ObjectType):
    cart = graphene.Field(CartType)
    success = graphene.Boolean()

class CreateAccountMutation(graphene.Mutation, LoginResultType):
    #
    # https://stackoverflow.com/questions/10372877/how-to-create-a-user-in-django
    # https://docs.djangoproject.com/en/2.0/ref/contrib/auth/#django.contrib.auth.models.UserManager.create_user
    #
    class Arguments:
        firstName = graphene.String(required=True)
        lastName = graphene.String(required=True)
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    def mutate(self, info, firstName, lastName, username, password):
        # Try to create a new user and calculate a token
        try:
            # Create new user object with bullshit password
            user = django.contrib.auth.models.User.objects.create_user (
                first_name = firstName,
                last_name = lastName,
                username = username,
                password = password)

            # Try saving it to db
            user.save()

            # Calculate the token (ffs)
            tok = graphql_jwt.shortcuts.get_token(user)

            # Hide password
            user.password = "Hidden"

            # Return the created user, success flag and token
            return CreateAccountMutation(user=user, success=True, token=tok)
        except:
            # Most likely, the user already exists
            # Return blank user and token with success set false
            return CreateAccountMutation(user=None, success=False, token="")

class LoginMutation(graphql_jwt.JSONWebTokenMutation, LoginResultType):
    @classmethod
    def resolve(cls, root, info):
        user = info.context.user
        user.password = "Hidden"
        return LoginMutation(user=user, success=True)

class BuyMutation(graphene.Mutation, ReceiptType):
    class Arguments:
        products = graphene.NonNull(graphene.List(graphene.ID))

    def mutate(self, info, **kwargs):
        # Check authentication first, if not logged in return unsuccessful buy
        if info.context.user.is_anonymous:
            return BuyMutation(cart=None, success=False)
        else:
            # Process the supplied product ids into a cart
            cart = CartType.processcart(kwargs['products'])

            # Create an order
            order = Order()
            order.totalBeforeDiscount = cart.totalBeforeDiscount
            order.totalDiscount = cart.totalDiscount
            order.total = cart.total
            order.user = info.context.user

            # Save the order
            order.save()

            # Set products
            products = []
            for x in cart.products:
                products = products + [x]
            order.products.set(products)

            # Return a successful buy operation
            return BuyMutation(cart=cart, success=True)

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
        if 'category' in filter and filter['category'] is not None and products is not None:
            categories = filter['category']
            qset = None
            for cat in categories:
                kw = {'category': cat}
                if qset is None:
                    qset = products.filter(**kw)
                else:
                    qset = qset | products.filter(**kw)
            products = qset

        if 'onSale' in filter and filter['onSale'] and products is not None:
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
        cart = CartType.processcart(kwargs['products'])
        return cart

class Mutation(graphene.ObjectType):
    createAccount = CreateAccountMutation.Field()
    login = LoginMutation.Field()
    buy = BuyMutation.Field()
