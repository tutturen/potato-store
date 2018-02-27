from django.contrib import admin
from products.models import Product, Category, User

# Register your models here.

class ProductAdmin(admin.ModelAdmin):
    pass

admin.site.register(Product, ProductAdmin)