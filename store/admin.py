from django.contrib import admin
from .models import Product, StoreBranch, Order, OrderDetail, Category, StockTransfer, UserProfile

# Đăng ký các model cũ
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(StoreBranch)
admin.site.register(Order)
admin.site.register(OrderDetail)
admin.site.register(StockTransfer)

# Đăng ký UserProfile để phân quyền
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'branch', 'phone')
    list_filter = ('role', 'branch')
    search_fields = ('user__username', 'phone')