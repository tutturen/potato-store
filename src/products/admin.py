from django.contrib import admin
from django.urls import path
from products.models import Product
from products.models import ProductPurchase
from products.models import Category
from products.models import User
from products.models import PercentSale
from products.models import PackageDeal
from products.models import Order
from products.admin_views import notify_user


class ProductsAdminSite(admin.AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        new_urls = [
            path('notify_user', self.admin_view(notify_user), {'admin': self}),
        ]
        return new_urls + urls
# TODO: Create custom actions for orders which redirects to notify_user view
# TODO: Create custom actions for users which redirects to notify_user view


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
        ('Pricing', {'fields': ['price', 'unitPrice', 'unit']}),
        ('Stock', {'fields': ['stockValue']})
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


our_admin = ProductsAdminSite()
our_admin.register(Category, CategoryAdmin)
our_admin.register(PercentSale, PercentSaleAdmin)
our_admin.register(PackageDeal, PackageDealAdmin)
our_admin.register(Product, ProductAdmin)
our_admin.register(User, UserAdmin)
our_admin.register(Order, OrderAdmin)
our_admin.register(ProductPurchase, ProductPurchaseAdmin)
