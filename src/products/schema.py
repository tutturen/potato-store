import graphene
import graphql_jwt
import django
from math import inf
from collections import defaultdict
from graphene_django.types import DjangoObjectType
from products.models import Category, Product, PercentSale, PackageDeal, Order


class CategoryType(DjangoObjectType):
    class Meta:
        model = Category


class UserType(DjangoObjectType):
    class Meta:
        model = django.contrib.auth.models.User


class PercentSaleType(DjangoObjectType):
    class Meta:
        model = PercentSale


class PackageDealType(DjangoObjectType):
    class Meta:
        model = PackageDeal


class ProductType(DjangoObjectType):
    percentSale = PercentSaleType
    packageDeal = PackageDealType

    class Meta:
        model = Product


class CartType(graphene.ObjectType):
    products = graphene.List(lambda: ProductType)
    totalBeforeDiscount = graphene.Float()
    totalDiscount = graphene.Float()
    total = graphene.Float()

    @staticmethod
    def find_sale_details(products, product_quantity,
                          product_pricing, product_packagedeal):
        dbproducts = []
        for product_id in products:
            # Find the product in the DB
            deal_product = Product.objects.filter(id=product_id)

            # Verify if product is valid
            if deal_product:
                deal_product = deal_product[0]
            else:
                continue

            # Add all to the result list
            dbproducts.append(deal_product)
            product_quantity[product_id] += 1

            # If the price has been calculated, skip the item
            if product_id in product_pricing:
                continue

            # Default price
            sale_price = deal_product.price

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

            # The first package deal is picked
            package_deals = PackageDeal.objects.filter(product=deal_product)
            if package_deals:
                product_packagedeal[product_id] = package_deals[0]

            # Summarize details per product
            product_pricing[product_id] = (deal_product.price, sale_price)

        return dbproducts

    @staticmethod
    def calculate_cart_price(cart, product_quantity,
                             product_packagedeal, product_pricing):
        for product in product_quantity:
            original_price, sale_price = product_pricing[product]
            quantity = product_quantity[product]

            pay_quantity = quantity
            # A product may or may not have an associated package deal
            if product in product_packagedeal:
                deal = product_packagedeal[product]

                discounted = quantity / deal.minimumQuantity
                discounted *= deal.paidQuantity
                discounted = int(discounted)

                remainder = quantity % deal.minimumQuantity

                pay_quantity = discounted + remainder

            cart.totalBeforeDiscount += original_price * quantity
            cart.total += sale_price * pay_quantity

    def processcart(products):
        # Create empty cart type
        cart = CartType(totalBeforeDiscount=0,
                        totalDiscount=0,
                        total=0)

        product_quantity = defaultdict(int)
        product_pricing = {}
        product_packagedeal = {}

        # Finding package deals and percent sales
        cart.products = CartType.find_sale_details(
            products, product_quantity,
            product_packagedeal, product_pricing
        )

        # At this point we have all information on the products
        CartType.calculate_cart_price(
            cart, product_quantity, product_pricing,
            product_packagedeal
        )

        cart.totalDiscount = cart.totalBeforeDiscount - cart.total

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
            # Check lengths
            if len(firstName) <= 0:
                print('Length of first name', len(firstName))
                raise Warning("No first name")

            if len(lastName) <= 0:
                print('Length of last name', len(lastName))
                raise Warning("No last name")

            if len(password) < 8:
                print('Length of password', len(password))
                raise Warning("Password too short")

            # Create new user object
            user = django.contrib.auth.models.User.objects.create_user(
                first_name=firstName,
                last_name=lastName,
                username=username,
                password=password)

            # Try saving it to db
            user.save()

            # Calculate the token (ffs)
            tok = graphql_jwt.shortcuts.get_token(user)

            # Hide password
            user.password = "Hidden"

            # Return the created user, success flag and token
            return CreateAccountMutation(user=user, success=True, token=tok)
        except Exception as e:
            # Print the exeption first
            print(e)

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
    # Query types
    all_categories = graphene.NonNull(
        graphene.List(graphene.NonNull(CategoryType)))

    all_products = graphene.Field(
        type=graphene.NonNull(graphene.List(graphene.NonNull(ProductType))),
        filter=graphene.Argument(FilterInputType))

    category = graphene.Field(CategoryType,
                              categoryName=graphene.String())

    cart = graphene.Field(CartType,
                          products=graphene.NonNull(
                              graphene.List(graphene.ID)))

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
                    qset = qset \
                        | products.filter(**{constraint: q[constraint]})

            products = qset

        # Check whether product's category is queried
        # We need to do a union on this field, but intersection
        # with previous results
        if ('category' in filter and
                filter['category'] is not None and
                products is not None):
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
            products = products.filter(percentSale__isnull=False) \
                | products.filter(packageDeal__isnull=False)

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
