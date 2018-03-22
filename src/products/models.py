import django
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User as DjangoUser


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class PercentSale(models.Model):
    product = models.ForeignKey(
        'Product',
        related_name='percent_sale',
        on_delete=models.CASCADE)
    cut = models.IntegerField("Cut in percent")

    def clean(self):
        if self.cut < 0:
            raise ValidationError("Percentage cannot be negative")
        elif self.cut == 0:
            msg = "For no sale, remove it in the product first"
            raise ValidationError(msg)
        elif not (0 < self.cut < 100):
            raise ValidationError("Percentage must be between 1 and 99")

    def save(self, *args, **kwargs):
        if 0 < self.cut < 100:
            super(PercentSale, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.product) + ' (' + str(self.cut) + '% sale)'


class PackageDeal(models.Model):
    product = models.ManyToManyField(
        'Product',
        related_name='package_deal')
    paidQuantity = models.IntegerField("You pay for")
    minimumQuantity = models.IntegerField("You buy")

    def clean(self):
        if self.paidQuantity <= 0 or self.minimumQuantity <= 0:
            raise ValidationError("Negative or zero values are not allowed")
        elif self.paidQuantity >= self.minimumQuantity:
            msg = "Minimum quantity must be greater than paid quantity"
            raise ValidationError(msg)

    def save(self, *args, **kwargs):
        if (self.minimumQuantity > 0 and
                0 < self.paidQuantity < self.minimumQuantity):
            super(PackageDeal, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.minimumQuantity) \
            + " for " \
            + str(self.paidQuantity) \
            + " on: " \
            + ", ".join(p.name for p in self.product.all())


class Product(models.Model):
    # Category, name, organic and notes
    name = models.CharField(max_length=100)
    subtitle = models.TextField()
    image = models.CharField(max_length=255)

    # Product pricing
    price = models.FloatField("Price per product")
    unitPrice = models.FloatField("Unit price")
    unit = models.CharField("Unit type", max_length=30)
    category = models.ForeignKey(
        Category,
        related_name='products',
        on_delete=models.CASCADE)
    organic = models.BooleanField()

    def clean(self):
        if self.percentSale and self.packageDeal:
            msg = 'You cannot have both deal types at the same time.'
            raise ValidationError(msg)

    def save(self, *args, **kwargs):
        if not self.percentSale:
            self.percentSale = None

        if not self.packageDeal:
            self.packageDeal = None

        if self.percentSale and self.packageDeal:
            pass
        else:
            super(Product, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class Order(models.Model):
    products = models.ManyToManyField(Product)
    totalBeforeDiscount = models.FloatField()
    totalDiscount = models.FloatField()
    total = models.FloatField()
    user = models.ForeignKey(
        DjangoUser,
        related_name='products',
        on_delete=models.CASCADE)

    def __str__(self):
        return 'This cart has ' \
            + str(self.products.count()) \
            + ' items, price total ' \
            + str(self.total) \
            + ' kr'


class Receipt(models.Model):
    success = models.BooleanField()
    order = models.ForeignKey(Order, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.order)


class User(models.Model):
    firstName = models.CharField("First name", max_length=100)
    lastName = models.CharField("Last name", max_length=100)
    username = models.CharField("Username", max_length=50)

    def save(self, *args, **kwargs):
        super(User, self).save(*args, **kwargs)

    # Customize the name shown in the admin panel
    def __str__(self):
        return self.firstName \
            + ' ' \
            + self.lastName \
            + ' (' + self.username + ')'
