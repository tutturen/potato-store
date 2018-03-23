import graphene
from math import inf
from products.models import Category
from products.models import Product
from products.schema_types import CartType
from products.schema_types import CategoryType
from products.schema_types import ProductType
from products.schema_types import FilterInputType
from products.schema_types import CartItemInput


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

    def resolve_all_products(self, info, filter={}):
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
