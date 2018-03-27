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
                sale_price *= (100 - max_deal.cut) / 100.

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


class FilterInputType(graphene.InputObjectType):
    text = graphene.String(required=False)
    minPrice = graphene.Float(required=False)
    maxPrice = graphene.Float(required=False)
    category = graphene.List(graphene.ID, required=False)
    onSale = graphene.Boolean(required=False)
    organic = graphene.Boolean(required=False)
