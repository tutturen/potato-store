from django.contrib import admin
from products.models import Product, Category, User, PercentSale, PackageDeal

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
        ('Product', {'fields': ['category', 'name', 'organic', 'notes']}),
        ('Pricing', {'fields': ['price', 'unitPrice', 'unit']}),
        ('Sale', {'fields': ['percentSale', 'packageDeal']})
    ]

admin.site.register(Category, CategoryAdmin)
admin.site.register(PercentSale, PercentSaleAdmin)
admin.site.register(PackageDeal, PackageDealAdmin)
admin.site.register(Product, ProductAdmin)
