from django.db import models
from django.core.exceptions import ValidationError

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class PercentSale(models.Model):
    product = models.ForeignKey('Product',
        on_delete=models.CASCADE
    )
    cut = models.IntegerField("Cut in percent")

    def clean(self):
        if self.cut < 0:
            raise ValidationError("Percentage cannot be negative")
        elif self.cut == 0:
            raise ValidationError("For no sale, remove it in the product first and then delete it here")
        elif not (self.cut > 0 and self.cut < 100):
            raise ValidationError("Percentage must be between 1 and 99")

    def save(self, *args, **kwargs):
        if self.cut > 0 and self.cut < 100:
            super(PercentSale, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.product)

class PackageDeal(models.Model):
    product = models.ManyToManyField('Product')
    paidQuantity = models.IntegerField("Paid quantity")
    minimumQuantity = models.IntegerField("Minimum quantity")

    def clean(self):
        if self.paidQuantity <= 0 or self.minimumQuantity <= 0:
            raise ValidationError("Negative or zero values are not allowed")
        elif self.paidQuantity >= self.minimumQuantity:
            raise ValidationError("Minimum quantity must be greater than paid quantity")

    def save(self, *args, **kwargs):
        if self.paidQuantity > 0 and self.minimumQuantity > 0 and self.paidQuantity < self.minimumQuantity:
            super(PackageDeal, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.product)

class Product(models.Model):
    # Category, name, organic and notes
    category = models.ForeignKey(Category,
        related_name='products',
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)
    organic = models.BooleanField()
    notes = models.TextField()

    # Product pricing
    price = models.FloatField("Price per product")
    unitPrice = models.FloatField("Unit price")
    unit = models.CharField("Unit type", max_length=30)

    # Sale types
    percentSale = models.ForeignKey(PercentSale,
        related_name='products',
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        verbose_name="Percentage-based sale"
        )
    packageDeal = models.ForeignKey(PackageDeal,
        related_name='products',
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        verbose_name="Package-deal based sale"
        )

    def clean(self):
        if self.percentSale and self.packageDeal:
            raise ValidationError('You cannot have both percentage sale and package deal at the same time.')

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

class Cart(models.Model):
    products = models.ManyToManyField(Product)
    totalBeforeDiscount = models.FloatField()
    totalDiscount = models.FloatField()
    total = models.FloatField()

    def __str__(self):
        return str(self.products)

class Receipt(models.Model):
    success = models.BooleanField()
    cart = models.ForeignKey(Cart,
        # related_name='products',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return str(self.cart)

class User(models.Model):
    firstName = models.CharField(max_length=100)
    lastName = models.CharField(max_length=100)
    username = models.CharField(max_length=50)
    cart = models.ForeignKey(Cart,
        # related_name='products',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.username

class LoginResult(models.Model):
    user = models.ForeignKey(User,
        on_delete=models.CASCADE
    )
    success = models.BooleanField()
    token = models.CharField(max_length=100)

    def __str__(self):
        return str(self.user) + str(self.token)
