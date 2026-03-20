from django.db import models
from django.contrib.auth.models import User

# 1. Bảng Danh mục
class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name="Tên danh mục")
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

# 2. Bảng Sản phẩm
class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', null=True, verbose_name="Danh mục")
    name = models.CharField(max_length=255, verbose_name="Tên sản phẩm")
    description = models.TextField(blank=True, null=True, verbose_name="Mô tả")
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Giá bán (VNĐ)")
    original_price = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True, verbose_name="Giá gốc (VNĐ)")
    image = models.ImageField(upload_to='products/', null=True, blank=True, verbose_name="Ảnh")
    is_flash_sale = models.BooleanField(default=False, verbose_name="Hàng Flash Sale")
    stock = models.IntegerField(default=0, verbose_name="Tồn kho")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_discount_percent(self):
        if self.original_price and self.original_price > self.price:
            return int(100 - (self.price / self.original_price * 100))
        return 0

# 3. Bảng Giỏ hàng
class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True) 
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

# 4. Bảng Đơn hàng tổng
class Order(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Sản phẩm")
    customer_name = models.CharField(max_length=100, verbose_name="Tên khách hàng")
    phone = models.CharField(max_length=20, verbose_name="Số điện thoại")
    address = models.TextField(verbose_name="Địa chỉ giao hàng")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày đặt")
    STATUS_CHOICES = [
        ('PENDING', 'Chờ xử lý'),
        ('DELIVERING', 'Đang giao hàng'),
        ('COMPLETED', 'Đã hoàn thành'),
        ('CANCELED', 'Đã hủy')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="Trạng thái")
    def __str__(self):
        return f"Đơn {self.id} - {self.customer_name} mua {self.product.name}"

# 5. Bảng Chi tiết Đơn hàng
class OrderDetail(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=0)

# 6. Bảng Chi nhánh 
class StoreBranch(models.Model):
    name = models.CharField(max_length=200, verbose_name="Tên chi nhánh")
    address = models.CharField(max_length=500, verbose_name="Địa chỉ")
    latitude = models.FloatField(verbose_name="Vĩ độ (Lat)") 
    longitude = models.FloatField(verbose_name="Kinh độ (Lon)")

    image = models.ImageField(upload_to='branches/', null=True, blank=True, verbose_name="Ảnh chi nhánh")
    STORE_TYPES = [('MAIN', 'Trụ sở chính'), ('SUB', 'Chi nhánh nhỏ')]
    store_type = models.CharField(max_length=10, choices=STORE_TYPES, default='SUB')

    def __str__(self):
        return self.name
    # ... (các model cũ giữ nguyên)

class StockTransfer(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    branch = models.ForeignKey(StoreBranch, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    transfer_type = models.CharField(max_length=50, default='XUẤT KHO')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Xuất {self.quantity} {self.product.name} cho {self.branch.name}"
