from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class PercentSale(models.Model):
    product = models.ForeignKey('Product',
        on_delete=models.CASCADE
    )
    cut = models.IntegerField()

    def __str__(self):
        return str(self.product)


class PackageDeal(models.Model):
    product = models.ManyToManyField('Product')
    paidQuantity = models.IntegerField()
    minimumQuantity = models.IntegerField()

    def __str__(self):
        return str(self.product)


class Product(models.Model):
    name = models.CharField(max_length=100)
    notes = models.TextField()
    category = models.ForeignKey(Category,
        related_name='products',
        on_delete=models.CASCADE
    )
    price = models.FloatField()
    unitPrice = models.FloatField()
    unit = models.CharField(max_length=30)
    organic = models.BooleanField()
    percentSale = models.ForeignKey(PercentSale,
        related_name='products',
        on_delete=models.DO_NOTHING,
        null=True
        )
    packageDeal = models.ForeignKey(PackageDeal,
        related_name='products',
        on_delete=models.DO_NOTHING,
        null=True
        )

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