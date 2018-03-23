import graphene
from products.schema_queries import Query
from products.schema_mutations import CreateAccountMutation
from products.schema_mutations import LoginMutation
from products.schema_mutations import BuyMutation


class Mutation(graphene.ObjectType):
    createAccount = CreateAccountMutation.Field()
    login = LoginMutation.Field()
    buy = BuyMutation.Field()
