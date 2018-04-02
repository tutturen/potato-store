import graphene
import graphql_jwt
import django
from products.models import Order
from products.models import ProductPurchase
from products.schema_types import CartType
from products.schema_types import CartItemInput
from products.schema_types import LoginResultType
from products.schema_types import ReceiptType


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
        email = graphene.String(required=True)

    def mutate(self, info, firstName, lastName, username, password, email):
        # TODO: Test creating new users with the new changes (email field)
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

            if not email or len(email) == 0:
                raise Warning("No email given")


            # Create new user object
            user = django.contrib.auth.models.User.objects.create_user(
                first_name=firstName,
                last_name=lastName,
                username=username,
                password=password,
                email=email,
            )

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
            for x in cart.items:
                purchase = ProductPurchase()
                purchase.product = x.product
                purchase.quantity = x.quantity
                purchase.unitPrice = x.unitPrice
                products = products + [purchase]
                purchase.save()

            order.products.set(products)

            # Return a successful buy operation
            return BuyMutation(cart=cart, success=True)
