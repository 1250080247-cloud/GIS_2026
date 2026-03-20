from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Product, StoreBranch, Order, OrderDetail, Category, StockTransfer
from .forms import ProductForm
from django.contrib.auth.decorators import login_required, user_passes_test
import json
from datetime import timedelta # <-- DÙNG ĐỂ TÍNH TOÁN THỜI GIAN GỘP ĐƠN
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login

# Hàm kiểm tra xem user có phải là Admin/Nhân viên không
def is_admin(user):
    return user.is_staff or user.is_superuser

# --- HÀM XỬ LÝ ĐẶT HÀNG NHANH ---
def process_order(request):
    product_id = request.POST.get('product_id')
    name = request.POST.get('name')
    phone = request.POST.get('phone')
    address = request.POST.get('address')
    
    san_pham = get_object_or_404(Product, id=product_id)
    
    # Bước 1: Tạo Đơn Hàng Tổng
    don_hang = Order.objects.create(
        customer_name=name,
        phone=phone,
        address=address,
        total_amount=san_pham.price # Tạm tính mua 1 món
    )
    
    # Bước 2: Tạo Chi tiết đơn hàng
    OrderDetail.objects.create(
        order=don_hang,
        product=san_pham,
        quantity=1,
        price=san_pham.price
    )
    
    # Bước 3: Trừ tồn kho
    if san_pham.stock > 0:
        san_pham.stock -= 1
        san_pham.save()

    messages.success(request, f"✅ Đã đặt thành công: {san_pham.name}!")

# --- TRANG CHỦ BÁN HÀNG ---
def landing_page(request):
    flash_deals = Product.objects.filter(is_flash_sale=True)
    all_products = Product.objects.all() 
    
    return render(request, 'store/landing.html', {
        'flash_deals': flash_deals,
        'all_products': all_products 
    })

# --- TRANG BẢN ĐỒ ---
def home(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        
        product = get_object_or_404(Product, id=product_id)
        
        Order.objects.create(
            product=product,
            customer_name=name,
            phone=phone,
            address=address
        )
        
        messages.success(request, f"🎉 Đặt hàng thành công: {product.name}!")
        request.session['last_order_address'] = address
        return redirect('map_page')

    branches = StoreBranch.objects.all()
    products = Product.objects.all()
    last_order_address = request.session.pop('last_order_address', None)
    
    return render(request, 'store/home.html', {
        'branches': branches, 
        'products': products,
        'last_order_address': last_order_address 
    })

# =====================================================================
# 1. ĐÃ CẬP NHẬT: GÓC QUẢN TRỊ (DASHBOARD) - CHỨC NĂNG GỘP ĐƠN
# =====================================================================
@login_required(login_url='login')
@user_passes_test(is_admin, login_url='landing')
def custom_dashboard(request):
    products = Product.objects.all()
    raw_orders = Order.objects.all().order_by('-created_at')
    
    # Logic Gộp các món hàng mua cùng lúc (cách nhau dưới 5 giây)
    grouped_orders = []
    current_group = None

    for order in raw_orders:
        if not current_group:
            current_group = {'main': order, 'extra_count': 0}
        else:
            # Tính khoảng cách thời gian giữa 2 đơn hàng
            time_diff = abs((current_group['main'].created_at - order.created_at).total_seconds())
            
            # Nếu cùng số điện thoại và cách nhau dưới 5 giây -> Cùng 1 giỏ hàng
            if order.phone == current_group['main'].phone and time_diff < 5:
                current_group['extra_count'] += 1
            else:
                grouped_orders.append(current_group)
                current_group = {'main': order, 'extra_count': 0}
                
    if current_group:
        grouped_orders.append(current_group)
    
    branches = StoreBranch.objects.all() 
    
    context = {
        'products': products,
        'orders': grouped_orders, # Truyền danh sách ĐÃ GỘP ra giao diện
        'total_products': products.count(),
        'total_orders': len(grouped_orders), # Tổng số đơn sau khi gộp
        'branches': branches, 
    }
    return render(request, 'store/dashboard.html', context)


# --- CHỨC NĂNG THÊM SẢN PHẨM ---
@login_required(login_url='login')
@user_passes_test(is_admin, login_url='landing')
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Đã thêm sản phẩm thành công!")
            return redirect('dashboard')
    else:
        form = ProductForm()
    return render(request, 'store/add_product.html', {'form': form})

# --- CHỨC NĂNG SỬA SẢN PHẨM ---
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"✅ Đã cập nhật thành công: {product.name}")
            return redirect('dashboard')
    else:
        form = ProductForm(instance=product)
    return render(request, 'store/edit_product.html', {'form': form, 'product': product})

# --- CHỨC NĂNG XÓA SẢN PHẨM ---
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f"🗑️ Đã xóa sản phẩm: {product_name}")
        return redirect('dashboard')
    return render(request, 'store/delete_product.html', {'product': product})

def product_detail(request, product_id):
    # 1. Tìm sản phẩm khách đang bấm vào
    product = get_object_or_404(Product, id=product_id)
    
    # 2. Tìm các sản phẩm CÙNG DANH MỤC, NHƯNG KHÁC ID (loại trừ sp hiện tại)
    # Lấy tối đa 4 món để dàn thành 1 hàng ngang cho đẹp
    related_products = Product.objects.filter(category=product.category).exclude(id=product_id)[:4]
    
    # 3. Truyền cả 2 biến này ra ngoài giao diện
    return render(request, 'store/product_detail.html', {
        'product': product,
        'related_products': related_products
    })

# --- QUẢN LÝ CHI NHÁNH ---
@login_required(login_url='login')
@user_passes_test(is_admin, login_url='landing')
def add_branch(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        store_type = request.POST.get('store_type')
        image = request.FILES.get('image') 
        
        StoreBranch.objects.create(
            name=name, address=address, latitude=latitude,
            longitude=longitude, store_type=store_type, image=image
        )
        messages.success(request, f"Đã thêm chi nhánh '{name}' thành công!")
        return redirect('dashboard')
    return render(request, 'store/add_branch.html')

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='landing')
def edit_branch(request, branch_id):
    branch = get_object_or_404(StoreBranch, id=branch_id)
    if request.method == 'POST':
        branch.name = request.POST.get('name')
        branch.address = request.POST.get('address')
        branch.latitude = request.POST.get('latitude')
        branch.longitude = request.POST.get('longitude')
        branch.store_type = request.POST.get('store_type')
        if request.FILES.get('image'):
            branch.image = request.FILES.get('image')
            
        branch.save()
        messages.success(request, f"Đã cập nhật chi nhánh '{branch.name}' thành công!")
        return redirect('dashboard')
    return render(request, 'store/edit_branch.html', {'branch': branch})

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='landing')
def delete_branch(request, branch_id):
    branch = get_object_or_404(StoreBranch, id=branch_id)
    branch.delete()
    messages.success(request, "Đã xóa chi nhánh khỏi hệ thống!")
    return redirect('dashboard')

# =====================================================================
# 2. ĐÃ CẬP NHẬT: HÀM IN HÓA ĐƠN (GỘP CHUNG 1 BILL)
# =====================================================================
@login_required(login_url='login')
@user_passes_test(is_admin, login_url='landing')
def order_invoice(request, order_id):
    main_order = get_object_or_404(Order, id=order_id)
    
    # Lấy toàn bộ các món hàng khách mua cùng lúc (Trong khoảng 5s)
    time_min = main_order.created_at - timedelta(seconds=5)
    time_max = main_order.created_at + timedelta(seconds=5)
    sibling_orders = Order.objects.filter(phone=main_order.phone, created_at__range=(time_min, time_max))
    
    # Tính tổng tiền
    total_price = sum(o.product.price for o in sibling_orders)
    
    return render(request, 'store/invoice.html', {
        'main_order': main_order,
        'sibling_orders': sibling_orders,
        'total_price': total_price
    })

# =====================================================================
# 3. ĐÃ CẬP NHẬT: HÀM ĐỔI TRẠNG THÁI (ĐỔI CHO TẤT CẢ MÓN TRONG GIỎ)
# =====================================================================
@login_required(login_url='login')
@user_passes_test(is_admin, login_url='landing')
def update_order_status(request, order_id):
    if request.method == 'POST':
        main_order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        
        # Tìm và cập nhật tất cả các món đồ trong cùng 1 giỏ hàng
        time_min = main_order.created_at - timedelta(seconds=5)
        time_max = main_order.created_at + timedelta(seconds=5)
        siblings = Order.objects.filter(phone=main_order.phone, created_at__range=(time_min, time_max))
        
        siblings.update(status=new_status)
        messages.success(request, f"Đã cập nhật trạng thái đơn hàng thành: {new_status}")
    return redirect('dashboard')

# --- HÀM THANH TOÁN GIỎ HÀNG (ĐÃ SỬA LỖI VẼ BẢN ĐỒ) ---
def checkout_cart(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        cart_data = request.POST.get('cart_data') 
        
        try:
            cart_items = json.loads(cart_data)
            if not cart_items:
                messages.error(request, "Giỏ hàng của bạn đang trống!")
                return redirect(request.META.get('HTTP_REFERER', 'landing'))
                
            for item in cart_items:
                product_id = item.get('id')
                product = Product.objects.get(id=product_id)
                
                Order.objects.create(
                    customer_name=name,
                    phone=phone,
                    address=address,
                    product=product,
                    status='Đang xử lý'
                )
            
            # ================= CẬP NHẬT Ở ĐÂY =================
            # 1. Lưu địa chỉ khách vừa nhập vào session để trang Bản đồ đọc được
            request.session['last_order_address'] = address
            
            messages.success(request, "🎉 Đặt hàng thành công! Hệ thống đang tìm tuyến đường giao hàng...")
            
            # 2. Bắt buộc chuyển hướng thẳng sang trang Bản đồ (thay vì ở lại trang cũ)
            return redirect('map_page')
            # ==================================================
            
        except Exception as e:
            messages.error(request, f"Có lỗi xảy ra: {str(e)}")
            
    return redirect(request.META.get('HTTP_REFERER', 'landing'))

# --- QUẢN LÝ TỒN KHO & XUẤT KHO (ĐÃ NÂNG CẤP XUẤT NHIỀU MÓN) ---
@login_required(login_url='login')
@user_passes_test(is_admin, login_url='landing')
def inventory_management(request):
    if request.method == 'POST':
        branch_id = request.POST.get('branch_id')
        transfer_data = request.POST.get('transfer_data') # Lấy danh sách món từ JS
        
        branch = get_object_or_404(StoreBranch, id=branch_id)
        
        try:
            items = json.loads(transfer_data)
            if not items:
                messages.error(request, "Danh sách xuất kho đang trống!")
                return redirect('inventory')
                
            first_transfer = None
            
            # Duyệt qua từng món trong danh sách xuất
            for item in items:
                product = Product.objects.get(id=item['product_id'])
                quantity = int(item['quantity'])
                
                if product.stock >= quantity:
                    # Trừ tồn kho
                    product.stock -= quantity
                    product.save()
                    
                    # Tạo lịch sử xuất
                    transfer = StockTransfer.objects.create(
                        product=product,
                        branch=branch,
                        quantity=quantity
                    )
                    # Giữ lại ID của món đầu tiên để chuyển trang in bill
                    if not first_transfer:
                        first_transfer = transfer
                else:
                    messages.warning(request, f"⚠️ Bỏ qua '{product.name}': Tồn kho ({product.stock}) không đủ xuất {quantity}!")
            
            if first_transfer:
                messages.success(request, f"✅ Đã lập Phiếu Xuất Kho thành công cho chi nhánh '{branch.name}'.")
                return redirect('export_invoice', transfer_id=first_transfer.id)
            else:
                return redirect('inventory')
                
        except Exception as e:
            messages.error(request, f"Lỗi xử lý: {str(e)}")
            return redirect('inventory')

    branches = StoreBranch.objects.filter(store_type='SUB')
    products = Product.objects.all()
    transfers = StockTransfer.objects.all().order_by('-created_at')
    
    return render(request, 'store/inventory.html', {
        'branches': branches,
        'products': products,
        'transfers': transfers
    })

# --- IN PHIẾU XUẤT KHO (ĐÃ NÂNG CẤP GỘP NHIỀU MÓN) ---
@login_required(login_url='login')
@user_passes_test(is_admin, login_url='landing')
def export_invoice(request, transfer_id):
    main_transfer = get_object_or_404(StockTransfer, id=transfer_id)
    
    # Lấy tất cả các món xuất cho cùng 1 chi nhánh, cùng 1 thời điểm (cách nhau 5s)
    time_min = main_transfer.created_at - timedelta(seconds=5)
    time_max = main_transfer.created_at + timedelta(seconds=5)
    sibling_transfers = StockTransfer.objects.filter(branch=main_transfer.branch, created_at__range=(time_min, time_max))
    
    return render(request, 'store/export_invoice.html', {
        'main_transfer': main_transfer,
        'sibling_transfers': sibling_transfers
    })

# --- CHỨC NĂNG ĐĂNG KÝ TÀI KHOẢN MỚI ---
def register_user(request):
    # Nếu đã đăng nhập rồi thì đá về trang chủ
    if request.user.is_authenticated:
        return redirect('landing')
        
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Tự động đăng nhập luôn sau khi tạo tài khoản thành công
            auth_login(request, user)
            messages.success(request, f"🎉 Chào mừng {user.username}! Đăng ký tài khoản thành công.")
            return redirect('landing')
        else:
            for field in form:
                for error in field.errors:
                    messages.error(request, f"{error}")
    else:
        form = UserCreationForm()
        
    return render(request, 'store/register.html', {'form': form})