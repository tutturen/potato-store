import graphene
import graphql_jwt
import django
from math import inf
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

        cart.products = dbproducts

        product_quantity = {}
        product_pricing = {}

        # For every product requested
        for productId in products:
            # Find the product in the DB
            deal_product = Product.objects.filter(id=productId)

            # Verify if product is valid
            if deal_product:
                deal_product = deal_product[0]
            else:
                continue

            # Add all to the result list
            dbproducts.append(deal_product)

            # Default price
            sale_price = deal_product.price

            cart.totalBeforeDiscount += deal_product.price

            deals = PercentSale.objects.filter(product=deal_product)

            max_deal = None
            for deal in deals:
                if max_deal is None:
                    max_deal = deal
                else:
                    if deal.cut > max_deal.cut:
                        max_deal = deal

            if max_deal is not None:
                sale_price *= max_deal.cut / 100.

            # At last add sum
            cart.totalDiscount += deal_product.price - sale_price
            cart.total += sale_price

        # Create lists: k is unique products, v is the frequency
        d = {x:dbproducts.count(x) for x in dbproducts}
        pairs = [(k, v) for (k, v) in d.items()]

        return cart

        # Loop through to find package deals
        for item in pairs:
            # Check if the item has a package deal
            if item[0].packageDeal:
                # Calculate how many times we have to apply it
                num = int(item[1] / item[0].packageDeal.minimumQuantity)

                # Calculate the number of items to reduce per deal
                rem = int(item[0].packageDeal.minimumQuantity - item[0].packageDeal.paidQuantity)

                # Multiply with number of deals
                torem = rem * num

                # Calculate the price value to remove
                value = torem * item[0].price

                # Add to discount and remove from total
                cart.totalDiscount += value
                cart.total -= value

        # Return cart with products
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
        def search_fields(filter_name, filter_value):
            if filter_name not in field_mappings:
                return {}

            kw = {}
            for mapping in field_mappings[filter_name]:
                if filter_value is None:
                    continue

                # Generate the filter
                if filter_name == 'text':
                    kw.update({mapping + '__icontains': filter_value.lower()})
                elif filter_name == 'minPrice':
                    kw.update({mapping + '__range': (filter_value, inf)})
                elif filter_name == 'maxPrice':
                    kw.update({mapping + '__range': (0, filter_value)})
                elif filter_name == 'organic':
                    kw.update({mapping: filter_value})

            return kw

        # For text field, we must perform a union of
        #  name and subtitle results
        # For other fields, just perform intersection of results
        products = Product.objects.all()
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
            
            if qset is not None:
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
