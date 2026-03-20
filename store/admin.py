from django.contrib import admin
from .models import Product, StoreBranch, Order  

admin.site.register(Product)
admin.site.register(StoreBranch)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'phone', 'product', 'created_at') 
    readonly_fields = ('created_at',)