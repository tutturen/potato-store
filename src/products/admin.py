from django.contrib import admin
from products.models import Product
from products.models import ProductPurchase
from products.models import Category
from products.models import User
from products.models import PercentSale
from products.models import PackageDeal
from products.models import Order


class CategoryAdmin(admin.ModelAdmin):
    # A category contains only a name, no need to customize
    pass


class PercentSaleAdmin(admin.ModelAdmin):
    # Too simple to customize, validation is done in models.py
    pass


class PackageDealAdmin(admin.ModelAdmin):
    # Too simple to customize, validation is done in models.py
    pass


class ProductAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Product', {'fields': [
            'category', 'name', 'organic', 'subtitle', 'image']}),
        ('Pricing', {'fields': ['price', 'unitPrice', 'unit']})
    ]


class UserAdmin(admin.ModelAdmin):
    fields = ['firstName', 'lastName', 'username', 'cart']
    readonly_fields = ['cart']

    def cart(self, obj):
        return 'Secrets! {}'.format(obj.cart)


class ProductPurchaseAdmin(admin.ModelAdmin):
    pass


class ProductPurchaseInline(admin.TabularInline):
    model = Order.products.through


class OrderAdmin(admin.ModelAdmin):
    exclude = ('products', )
    inlines = (ProductPurchaseInline, )


admin.site.register(Category, CategoryAdmin)
admin.site.register(PercentSale, PercentSaleAdmin)
admin.site.register(PackageDeal, PackageDealAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(ProductPurchase, ProductPurchaseAdmin)
