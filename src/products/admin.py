from django.contrib import admin
import django.contrib.auth.models
import django.contrib.auth.admin
from django.urls import path
from django.http import HttpResponseRedirect
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


def notify_users_from_order(modeladmin, request, queryset):
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    orders = Order.objects.filter(pk__in=selected)
    users = map(lambda o: o.user, orders)
    user_ids = map(lambda u: u.pk, users)
    user_ids = map(str, user_ids)
    return HttpResponseRedirect("/admin/notify_user?u=%s" % ",".join(user_ids))
notify_users_from_order.short_description = "Send email to selected users from order"


def notify_users_from_userlist(modeladmin, request, queryset):
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    return HttpResponseRedirect("/admin/notify_user?u=%s" % ",".join(selected))
notify_users_from_userlist.short_description = "Send email to selected users from userlist"


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


class UserAdmin(django.contrib.auth.admin.UserAdmin):
    actions = [notify_users_from_userlist]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ProductPurchaseAdmin(admin.ModelAdmin):
    pass


class ProductPurchaseInline(admin.TabularInline):
    model = Order.products.through


class OrderAdmin(admin.ModelAdmin):
    exclude = ('products', )
    inlines = (ProductPurchaseInline, )
    actions = [notify_users_from_order]


our_admin = ProductsAdminSite()
our_admin.register(Category, CategoryAdmin)
our_admin.register(PercentSale, PercentSaleAdmin)
our_admin.register(PackageDeal, PackageDealAdmin)
our_admin.register(Product, ProductAdmin)
our_admin.register(Order, OrderAdmin)
our_admin.register(ProductPurchase, ProductPurchaseAdmin)

our_admin.register(django.contrib.auth.models.Group,
                   django.contrib.auth.admin.GroupAdmin)
our_admin.register(django.contrib.auth.models.User,
                   UserAdmin)
