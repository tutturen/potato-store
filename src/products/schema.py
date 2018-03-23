import graphene
import graphql_jwt
import django
from math import inf
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


class CartItem(graphene.ObjectType):
    product = graphene.NonNull(ProductType)
    quantity = graphene.NonNull(graphene.Int)
    unitPrice = graphene.NonNull(graphene.Float)
    originalPrice = graphene.NonNull(graphene.Float)


class CartItemInput(graphene.InputObjectType):
    product = graphene.NonNull(graphene.ID)
    quantity = graphene.NonNull(graphene.Int)


class CartType(graphene.ObjectType):
    items = graphene.List(CartItem)
    totalBeforeDiscount = graphene.Float()
    totalDiscount = graphene.Float()
    total = graphene.Float()

    @staticmethod
    def find_sale_details(product_quantity, product_pricing,
                          product_packagedeal):
        dbproducts = {}
        for product_id in product_quantity:
            # Find the product in the DB
            deal_product = Product.objects.filter(id=product_id)

            # Verify if product is valid
            if deal_product:
                deal_product = deal_product[0]
            else:
                continue

            # Add all to the result list
            if product_id in dbproducts:
                raise ValueError('Duplicate items')
            item = CartItem()
            item.product = deal_product
            item.quantity = product_quantity[product_id]
            dbproducts[product_id] = item

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

        return list(dbproducts.values())

    @staticmethod
    def calculate_cart_price(cart, product_quantity,
                             product_pricing, product_packagedeal):
        for product in product_quantity:
            original_price, sale_price = product_pricing[product]
            quantity = product_quantity[product]

            pay_quantity = quantity
            # A product may or may not have an associated package deal
            if product in product_packagedeal:
                deal = product_packagedeal[product]

                discounted = int(quantity / deal.minimumQuantity)
                discounted *= deal.paidQuantity
                discounted = int(discounted)

                remainder = quantity % deal.minimumQuantity

                pay_quantity = discounted + remainder
                product_pricing[product] = (
                    original_price,
                    (sale_price * pay_quantity) / quantity
                )

            cart.totalBeforeDiscount += original_price * quantity
            cart.total += sale_price * pay_quantity

    @staticmethod
    def processcart(products):
        # Create empty cart type
        cart = CartType(totalBeforeDiscount=0,
                        totalDiscount=0,
                        total=0)

        product_quantity = {
            item['product']: item['quantity']
            for item in products
        }
        product_pricing = {}
        product_packagedeal = {}

        # Finding package deals and percent sales
        cart.items = CartType.find_sale_details(
            product_quantity, product_pricing,
            product_packagedeal
        )

        # At this point we have all information on the products
        CartType.calculate_cart_price(
            cart, product_quantity, product_pricing,
            product_packagedeal
        )

        for item in cart.items:
            key = str(item.product.id)
            item.unitPrice = product_pricing[key][1]
            item.originalPrice = product_pricing[key][0]

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
        products = graphene.NonNull(graphene.List(CartItemInput))

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
                              graphene.List(CartItemInput)))

    # Create a kwargs object that can be filtered with,
    #  relational operators vary per field
    @staticmethod
    def create_keyword_query(filter_name, filter_value):
        field_mappings = {
            'text': ['name', 'subtitle'],
            'minPrice': ['price'],
            'maxPrice': ['price'],
            'organic': ['organic']
        }

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

    @staticmethod
    def filter_fields(products, product_filter):
        # First phase of filtering is to check single-field
        #  values of the filter
        for field in product_filter:
            q = Query.create_keyword_query(field, product_filter[field])
            # If no filter was created, skip
            # Otherwise we get empty results
            if len(q) == 0:
                continue
            select_set = None
            for constraint in q:
                if select_set is None:
                    select_set = products.filter(**{constraint: q[constraint]})
                else:
                    select_set = select_set \
                        | products.filter(**{constraint: q[constraint]})

            products = select_set
        return products

    @staticmethod
    def filter_sales(products, product_filter):
        if 'onSale' in product_filter and \
                product_filter['onSale'] and \
                products is not None:

            products.select_related('percent_sale')
            products.select_related('package_deal')

            products = products.filter(percent_sale__isnull=False) \
                | products.filter(package_deal__isnull=False)
        return products

    @staticmethod
    def filter_categories(products, product_filter):
        # Check whether product's category is queried
        # We need to do a union on this field, but intersection
        # with previous results
        if 'category' in product_filter and \
                product_filter['category'] is not None and \
                products is not None:
            categories = product_filter['category']
            select_set = None
            for cat in categories:
                kw = {'category': cat}
                if select_set is None:
                    select_set = products.filter(**kw)
                else:
                    select_set = select_set | products.filter(**kw)

            if select_set is not None:
                products = select_set
        return products

    def resolve_all_categories(self, info):
        return Category.objects.all()

    def resolve_all_products(self, info, filter):
        # For text field, we must perform a union of
        #  name and subtitle results
        # For other fields, just perform intersection of results
        products = Product.objects.all()

        products = Query.filter_fields(products, filter)
        products = Query.filter_categories(products, filter)
        products = Query.filter_sales(products, filter)

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
