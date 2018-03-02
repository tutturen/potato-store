import graphene
import graphql_jwt
import django
from graphene_django.types import DjangoObjectType
from products.models import Category, Product, User, PercentSale, PackageDeal

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

class ObtainJSONWebToken(graphql_jwt.JSONWebTokenMutation):
    user = graphene.Field(UserType)

    @classmethod
    def resolve(cls, root, info):
        return cls(user=info.context.user)

class LoginMutation(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    result = graphene.Field(LoginResultType)

    def mutate(self, info, username, password):
        pass
        #try:
        #user = {'username': input['username'], 'password': input['password']}
        #serializer = JSONWebTokenSerializer(data=user)
        #if serializer.is_valid():
        #    token = serializer.object['token']
        #    user = serializer.object['user']
        #    result = LoginResultType(success=True, token=token, user=user)
        #    return LoginMutation(result=result)
        #else:
        #    result = LoginResultType(success=False)
        #    return LoginMutatuon(result=result)
        #except:
        #    print("Error logging in")

class FilterInputType(graphene.InputObjectType):
    text = graphene.String(required=False)
    minPrice = graphene.Int(required=False)
    maxPrice = graphene.Int(required=False)
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
            'text': ['name', 'subtitle']
        }

        def search_fields(products, filterName, filterValue):
            if filterName not in field_mappings:
                return products

            for mapping in field_mappings[filterName]:
                kw = {mapping + '__contains': filterValue}
                products = products.filter(**kw)

            return products

        # We can easily optimize query count in the resolve method
        products = Product.objects.all()
        for field in filter:
            print(field, filter[field])
            products = search_fields(products, field, filter[field])

        print(type(products))
        return Product.objects.select_related('category').all()

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
    #login = LoginMutation.Field()
    login = ObtainJSONWebToken.Field()
