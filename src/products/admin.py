from django.contrib import admin
from products.models import Product, Category, User, PercentSale, PackageDeal

class CategoryAdmin(admin.ModelAdmin):
    pass

class ProductAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Product', {'fields': ['category', 'name', 'organic', 'notes']}),
        ('Pricing', {'fields': ['price', 'unitPrice', 'unit']}),
        ('Sale', {'fields': ['percentSale', 'packageDeal']})
    ]

class PercentSaleAdmin(admin.ModelAdmin):
    pass

class PackageDealAdmin(admin.ModelAdmin):
    pass

admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(PercentSale, PercentSaleAdmin)
admin.site.register(PackageDeal, PackageDealAdmin)
