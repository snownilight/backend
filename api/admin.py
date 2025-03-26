from django.contrib import admin
from .models import Category, Product, Warehouse, Inventory, StockMovement

# Register your models here.
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Warehouse)
admin.site.register(Inventory)
admin.site.register(StockMovement)
