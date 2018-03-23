import graphene
import django
from collections import defaultdict
from graphene_django.types import DjangoObjectType
from products.models import Category, Product, PercentSale, PackageDeal


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


class FilterInputType(graphene.InputObjectType):
    text = graphene.String(required=False)
    minPrice = graphene.Float(required=False)
    maxPrice = graphene.Float(required=False)
    category = graphene.List(graphene.ID, required=False)
    onSale = graphene.Boolean(required=False)
    organic = graphene.Boolean(required=False)
