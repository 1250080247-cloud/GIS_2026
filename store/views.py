import pandas as pd
from datetime import timedelta
import json
import unicodedata

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import make_password
from django.db.models import Q
from django.contrib.auth import update_session_auth_hash

from .models import Product, StoreBranch, Order, OrderDetail, Category, StockTransfer, UserProfile
from .forms import ProductForm

# =====================================================================
# HÀM BỔ TRỢ
# =====================================================================
# Hàm kiểm tra xem user có phải là Admin/Nhân viên không
def is_admin(user):
    return user.is_staff or user.is_superuser


# =====================================================================
# TRANG GIAO DIỆN KHÁCH HÀNG (FRONTEND)
# =====================================================================
def landing_page(request):
    flash_deals = Product.objects.filter(is_flash_sale=True)
    all_products = Product.objects.all() 
    return render(request, 'store/landing.html', {
        'flash_deals': flash_deals,
        'all_products': all_products 
    })

def search_results(request):
    query = request.GET.get('q', '').strip()
    
    # Nếu khách để trống ô tìm kiếm mà lỡ bấm Enter thì đá về trang chủ
    if not query:
        return redirect('landing')
        
    # 1. TÌM KIẾM TUYỆT ĐỐI (Khớp 100% tên sản phẩm - Không phân biệt hoa/thường)
    exact_match = Product.objects.filter(name__iexact=query).first()
    if exact_match:
        # Nếu gõ đúng 100% tên -> Bay thẳng vào trang chi tiết sản phẩm
        return redirect('product_detail', product_id=exact_match.id)
        
    # 2. TÌM KIẾM TƯƠNG ĐỐI (Chứa một phần từ khóa)
    products = Product.objects.filter(
        Q(name__icontains=query) | 
        Q(category__name__icontains=query)
    ).distinct()
    
    # Render ra trang danh sách kết quả
    return render(request, 'store/search_results.html', {
        'products': products,
        'search_query': query
    })

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    related_products = Product.objects.filter(category=product.category).exclude(id=product_id)[:4]
    
    return render(request, 'store/product_detail.html', {
        'product': product,
        'related_products': related_products
    })

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
# XỬ LÝ ĐƠN HÀNG (GIỎ HÀNG & MUA NHANH)
# =====================================================================
def process_order(request):
    product_id = request.POST.get('product_id')
    name = request.POST.get('name')
    phone = request.POST.get('phone')
    address = request.POST.get('address')
    
    san_pham = get_object_or_404(Product, id=product_id)
    
    don_hang = Order.objects.create(
        customer_name=name,
        phone=phone,
        address=address,
        total_amount=san_pham.price
    )
    
    OrderDetail.objects.create(
        order=don_hang,
        product=san_pham,
        quantity=1,
        price=san_pham.price
    )
    
    if san_pham.stock > 0:
        san_pham.stock -= 1
        san_pham.save()

    messages.success(request, f"✅ Đã đặt thành công: {san_pham.name}!")
    return redirect('landing')

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
            
            request.session['last_order_address'] = address
            messages.success(request, "🎉 Đặt hàng thành công! Hệ thống đang tìm tuyến đường giao hàng...")
            return redirect('map_page')
            
        except Exception as e:
            messages.error(request, f"Có lỗi xảy ra: {str(e)}")
            
    return redirect(request.META.get('HTTP_REFERER', 'landing'))


# =====================================================================
# TRANG QUẢN TRỊ DASHBOARD
# =====================================================================
@login_required(login_url='login')
@user_passes_test(is_admin, login_url='landing')
def custom_dashboard(request):
    
    # 1. TỰ ĐỘNG TẠO PROFILE CHO CÁC TÀI KHOẢN CŨ
    for u in User.objects.all():
        profile, created = UserProfile.objects.get_or_create(user=u)
        if created and u.is_superuser:
            profile.role = 'SUPERADMIN'
            profile.save()

    # 2. LẤY DANH SÁCH SẢN PHẨM & CHI NHÁNH
    products = Product.objects.all()
    branches = StoreBranch.objects.all() 

    # 3. LẤY VÀ GỘP ĐƠN HÀNG
    raw_orders = Order.objects.all().order_by('-created_at')
    grouped_orders = []
    current_group = None

    for order in raw_orders:
        if not current_group:
            current_group = {'main': order, 'extra_count': 0}
        else:
            time_diff = abs((current_group['main'].created_at - order.created_at).total_seconds())
            if order.phone == current_group['main'].phone and time_diff < 5:
                current_group['extra_count'] += 1
            else:
                grouped_orders.append(current_group)
                current_group = {'main': order, 'extra_count': 0}
                
    if current_group:
        grouped_orders.append(current_group)

    # 4. TÍNH TOÁN THỐNG KÊ ĐƠN HÀNG VÀ DOANH THU
    pending_orders = 0
    shipping_orders = 0
    completed_orders = 0
    cancelled_orders = 0
    total_revenue = 0

    for group in grouped_orders:
        status = group['main'].status
        if status == 'Đang xử lý':
            pending_orders += 1
        elif status == 'Đang giao':
            shipping_orders += 1
        elif status == 'Đã giao':
            completed_orders += 1
        elif status == 'Đã hủy':
            cancelled_orders += 1

    for order in raw_orders:
        if order.status == 'Đã giao' and order.product:
            total_revenue += order.product.price

    formatted_revenue = "{:,.0f}".format(total_revenue).replace(',', '.')

    # 5. LẤY DANH SÁCH NGƯỜI DÙNG ĐỂ HIỂN THỊ PHÂN QUYỀN
    users_list = UserProfile.objects.all().select_related('user', 'branch')
    
    # 6. KIỂM TRA QUYỀN TRUY CẬP HIỆN TẠI
    current_role = 'CUSTOMER'
    if hasattr(request.user, 'profile'):
        current_role = request.user.profile.role
    elif request.user.is_superuser:
        current_role = 'SUPERADMIN'

    # ĐÓNG GÓI TẤT CẢ TRUYỀN RA GIAO DIỆN
    context = {
        'products': products,
        'orders': grouped_orders,
        'total_products': products.count(),
        'total_orders': len(grouped_orders),
        'branches': branches, 
        'users_list': users_list,
        'current_role': current_role,
        'pending_orders': pending_orders,
        'shipping_orders': shipping_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
        'total_revenue': formatted_revenue,
    }
    return render(request, 'store/dashboard.html', context)


# =====================================================================
# QUẢN LÝ TÀI KHOẢN (THÊM, SỬA, XÓA ROLE)
# =====================================================================
@login_required(login_url='login')
@user_passes_test(is_admin, login_url='landing')
def create_internal_user(request):
    if request.method == 'POST':
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'SUPERADMIN':
            messages.error(request, "Cảnh báo: Bạn không có quyền tạo tài khoản!")
            return redirect('dashboard')

        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        role = request.POST.get('role')
        branch_id = request.POST.get('branch_id')

        if User.objects.filter(username=username).exists():
            messages.error(request, f"Tên đăng nhập '{username}' đã có người sử dụng!")
            return redirect('dashboard')

        user = User.objects.create(
            username=username,
            email=email,
            password=make_password(password),
            is_staff=True if role in ['SUPERADMIN', 'BRANCHADMIN', 'STAFF'] else False,
            is_superuser=True if role == 'SUPERADMIN' else False
        )

        profile = user.profile
        profile.role = role
        profile.phone = phone
        if branch_id:
            profile.branch_id = branch_id
        profile.save()

        messages.success(request, f"🎉 Đã tạo tài khoản {username} ({role}) thành công!")
    return redirect('dashboard')

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='landing')
def edit_user(request, user_id):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'SUPERADMIN':
        messages.error(request, "Cảnh báo: Bạn không có quyền chỉnh sửa tài khoản!")
        return redirect('dashboard')

    target_user = get_object_or_404(User, id=user_id)
    profile = target_user.profile
    branches = StoreBranch.objects.all()

    if request.method == 'POST':
        new_username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        role = request.POST.get('role')
        branch_id = request.POST.get('branch_id')

        if User.objects.filter(username=new_username).exclude(id=user_id).exists():
            messages.error(request, f"Tên đăng nhập '{new_username}' đã có người khác dùng!")
            return redirect('edit_user', user_id=user_id)

        target_user.username = new_username
        target_user.email = email
        target_user.is_staff = True if role in ['SUPERADMIN', 'BRANCHADMIN', 'STAFF'] else False
        target_user.is_superuser = True if role == 'SUPERADMIN' else False
        target_user.save()

        profile.phone = phone
        profile.role = role
        
        if role in ['BRANCHADMIN', 'STAFF'] and branch_id:
            profile.branch_id = branch_id
        else:
            profile.branch = None
            
        profile.save()

        messages.success(request, f"✅ Đã cập nhật thông tin & phân quyền cho: {target_user.username}")
        return redirect('dashboard')

    return render(request, 'store/edit_user.html', {
        'target_user': target_user,
        'profile': profile,
        'branches': branches
    })

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='landing')
def delete_user(request, user_id):
    if request.method == 'POST':
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'SUPERADMIN':
            messages.error(request, "Cảnh báo: Bạn không có quyền xóa tài khoản!")
            return redirect('dashboard')

        target_user = get_object_or_404(User, id=user_id)

        if target_user.id == request.user.id:
            messages.error(request, "❌ Bạn không thể tự xóa tài khoản của chính mình!")
            return redirect('dashboard')

        username = target_user.username
        target_user.delete()
        messages.success(request, f"🗑️ Đã xóa vĩnh viễn tài khoản: {username}")
        
    return redirect('dashboard')


# =====================================================================
# QUẢN LÝ SẢN PHẨM (THÊM, SỬA, XÓA, NHẬP EXCEL)
# =====================================================================
@login_required(login_url='login')
@user_passes_test(is_admin, login_url='landing')
def add_product(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price')
        
        original_price = request.POST.get('original_price')
        if not original_price:
            original_price = None

        stock = request.POST.get('stock')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        capacity = request.POST.get('capacity')
        manufacturer = request.POST.get('manufacturer')
        origin = request.POST.get('origin')
        is_flash_sale = request.POST.get('is_flash_sale') == 'on'
        
        image = request.FILES.get('image') 
        image_url = request.POST.get('image_url')
        
        secondary_image_links = request.POST.get('secondary_image_links')
        secondary_files = request.FILES.getlist('secondary_image_files') 
        
        image2 = None
        image3 = None
        if len(secondary_files) > 0:
            image2 = secondary_files[0]
        if len(secondary_files) > 1:
            image3 = secondary_files[1]
        
        category = Category.objects.get(id=category_id)
        product = Product(
            name=name,
            price=price,
            original_price=original_price,
            stock=stock,
            category=category,
            description=description,
            capacity=capacity,
            manufacturer=manufacturer,
            origin=origin,
            is_flash_sale=is_flash_sale,
            image=image, 
            image_url=image_url,
            image2=image2,
            image3=image3,
            secondary_image_links=secondary_image_links
        )
        product.save() 

        messages.success(request, '🎉 Thêm sản phẩm vào kho thành công!')
        return redirect('dashboard')
    
    return render(request, 'store/add_product.html')

# =====================================================================
# CHỨC NĂNG SỬA SẢN PHẨM
# =====================================================================
@login_required(login_url='login')
@user_passes_test(is_admin, login_url='landing')
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # BỔ SUNG: Lấy toàn bộ danh mục để hiển thị ở Dropdown
    categories = Category.objects.all() 
    
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.price = request.POST.get('price')
        
        original_price = request.POST.get('original_price')
        if original_price:
            product.original_price = original_price
        else:
            product.original_price = None
            
        product.stock = request.POST.get('stock')
        product.description = request.POST.get('description')
        product.capacity = request.POST.get('capacity')
        product.manufacturer = request.POST.get('manufacturer')
        product.origin = request.POST.get('origin')
        
        # BẮT DỮ LIỆU DANH MỤC TỪ FORM
        category_id = request.POST.get('category')
        if category_id:
            product.category = Category.objects.get(id=category_id)
            
        product.is_flash_sale = request.POST.get('is_flash_sale') == 'on'
        
        if request.FILES.get('image'):
            product.image = request.FILES.get('image')
        
        if request.POST.get('image_url'):
            product.image_url = request.POST.get('image_url')
            
        secondary_files = request.FILES.getlist('secondary_image_files')
        if len(secondary_files) > 0:
            product.image2 = secondary_files[0]
        if len(secondary_files) > 1:
            product.image3 = secondary_files[1]
            
        if request.POST.get('secondary_image_links') is not None:
            product.secondary_image_links = request.POST.get('secondary_image_links')
            
        product.save()
        messages.success(request, f"✅ Đã cập nhật thành công: {product.name}")
        return redirect('dashboard')
        
    # Gói thêm 'categories' gửi ra giao diện
    return render(request, 'store/edit_product.html', {
        'product': product,
        'categories': categories 
    })

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='landing')
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f"🗑️ Đã xóa sản phẩm: {product_name}")
        return redirect('dashboard')
    return render(request, 'store/delete_product.html', {'product': product})

# =====================================================================
# QUẢN LÝ CHI NHÁNH
# =====================================================================
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
# CHỨC NĂNG IN HÓA ĐƠN & ĐỔI TRẠNG THÁI ĐƠN HÀNG
# =====================================================================
@login_required(login_url='login')
@user_passes_test(is_admin, login_url='landing')
def order_invoice(request, order_id):
    main_order = get_object_or_404(Order, id=order_id)
    time_min = main_order.created_at - timedelta(seconds=5)
    time_max = main_order.created_at + timedelta(seconds=5)
    sibling_orders = Order.objects.filter(phone=main_order.phone, created_at__range=(time_min, time_max))
    
    total_price = sum(o.product.price for o in sibling_orders)
    
    return render(request, 'store/invoice.html', {
        'main_order': main_order,
        'sibling_orders': sibling_orders,
        'total_price': total_price
    })

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='landing')
def update_order_status(request, order_id):
    if request.method == 'POST':
        main_order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        
        time_min = main_order.created_at - timedelta(seconds=5)
        time_max = main_order.created_at + timedelta(seconds=5)
        siblings = Order.objects.filter(phone=main_order.phone, created_at__range=(time_min, time_max))
        
        siblings.update(status=new_status)
        messages.success(request, f"Đã cập nhật trạng thái đơn hàng thành: {new_status}")
    return redirect('dashboard')


# =====================================================================
# QUẢN LÝ TỒN KHO & XUẤT KHO
# =====================================================================
@login_required(login_url='login')
@user_passes_test(is_admin, login_url='landing')
def inventory_management(request):
    if request.method == 'POST':
        branch_id = request.POST.get('branch_id')
        transfer_data = request.POST.get('transfer_data') 
        
        branch = get_object_or_404(StoreBranch, id=branch_id)
        
        try:
            items = json.loads(transfer_data)
            if not items:
                messages.error(request, "Danh sách xuất kho đang trống!")
                return redirect('inventory')
                
            first_transfer = None
            
            for item in items:
                product = Product.objects.get(id=item['product_id'])
                quantity = int(item['quantity'])
                
                if product.stock >= quantity:
                    product.stock -= quantity
                    product.save()
                    
                    transfer = StockTransfer.objects.create(
                        product=product,
                        branch=branch,
                        quantity=quantity
                    )
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

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='landing')
def export_invoice(request, transfer_id):
    main_transfer = get_object_or_404(StockTransfer, id=transfer_id)
    time_min = main_transfer.created_at - timedelta(seconds=5)
    time_max = main_transfer.created_at + timedelta(seconds=5)
    sibling_transfers = StockTransfer.objects.filter(branch=main_transfer.branch, created_at__range=(time_min, time_max))
    
    return render(request, 'store/export_invoice.html', {
        'main_transfer': main_transfer,
        'sibling_transfers': sibling_transfers
    })


# =====================================================================
# ĐĂNG KÝ TÀI KHOẢN KHÁCH HÀNG
# =====================================================================
def register_user(request):
    if request.user.is_authenticated:
        return redirect('landing')
        
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
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
# =====================================================================
# TRANG QUẢN LÝ TÀI KHOẢN KHÁCH HÀNG (SHOPEE STYLE)
# =====================================================================
@login_required(login_url='login')
def customer_profile(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)

    # 1. XỬ LÝ CẬP NHẬT THÔNG TIN HỒ SƠ
    if request.method == 'POST':
        # Khách hàng bấm nút Lưu
        user.email = request.POST.get('email', '')
        user.save()
        
        profile.phone = request.POST.get('phone', '')
        profile.save()
        
        messages.success(request, "✅ Đã cập nhật hồ sơ thành công!")
        return redirect('customer_profile')

    # 2. LẤY LỊCH SỬ ĐƠN HÀNG (Dựa theo số điện thoại của tài khoản)
    my_orders = []
    if profile.phone:
        raw_orders = Order.objects.filter(phone=profile.phone).order_by('-created_at')
        
        # Gộp đơn hàng giống như cách làm ở Dashboard
        current_group = None
        for order in raw_orders:
            if not current_group:
                current_group = {'main': order, 'extra_count': 0}
            else:
                time_diff = abs((current_group['main'].created_at - order.created_at).total_seconds())
                if order.phone == current_group['main'].phone and time_diff < 5:
                    current_group['extra_count'] += 1
                else:
                    my_orders.append(current_group)
                    current_group = {'main': order, 'extra_count': 0}
        if current_group:
            my_orders.append(current_group)

    return render(request, 'store/profile.html', {
        'profile': profile,
        'my_orders': my_orders
    })
# =====================================================================
# TÍNH NĂNG: ĐỔI MẬT KHẨU TÀI KHOẢN
# =====================================================================
@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # 1. Kiểm tra mật khẩu cũ có đúng không
        if not request.user.check_password(old_password):
            messages.error(request, "❌ Mật khẩu hiện tại không chính xác!")
            return redirect('customer_profile')
        
        # 2. Kiểm tra mật khẩu mới có khớp nhau không
        if new_password != confirm_password:
            messages.error(request, "❌ Mật khẩu xác nhận không trùng khớp!")
            return redirect('customer_profile')
            
        # 3. Tiến hành đổi mật khẩu
        request.user.set_password(new_password)
        request.user.save()
        
        # Cập nhật lại session để user không bị văng ra ngoài bắt đăng nhập lại
        update_session_auth_hash(request, request.user) 
        
        messages.success(request, "✅ Đổi mật khẩu thành công! Tài khoản của bạn đã được bảo mật hơn.")
        
    return redirect('customer_profile')

def import_products_excel(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        
        try:
            df = pd.read_excel(excel_file).fillna('')
            count_new = 0     # Đếm SP tạo mới
            count_update = 0  # Đếm SP được cập nhật
            
            # LẤY TOÀN BỘ SẢN PHẨM LÊN ĐỂ SO SÁNH BẰNG PYTHON
            # (Cách này lách được mọi lỗi khoảng trắng hay Unicode của Database)
            all_products = list(Product.objects.all())
            
            for index, row in df.iterrows():
                name_excel = str(row.get('Tên sản phẩm', '')).strip()
                if not name_excel: 
                    continue 
                
                price = row.get('Giá bán', 0)
                original_price = row.get('Giá gốc', '')
                stock = row.get('Tồn kho', 0)
                category_name = str(row.get('Tên danh mục', '')).strip()
                
                try: price = int(price)
                except: price = 0
                
                try: stock = int(stock)
                except: stock = 0
                
                try: original_price = int(original_price) if original_price else None
                except: original_price = None

                # Xử lý Danh mục
                category = None
                if category_name:
                    category = Category.objects.filter(name__iexact=category_name).first()
                    if not category:
                        category = Category.objects.create(name=category_name)
                
                # ========================================================
                # LOGIC SO SÁNH TUYỆT ĐỐI (TRỊ MỌI LỖI KHOẢNG TRẮNG DƯ THỪA)
                # ========================================================
                # Hàm này biến "Sữa   Rửa Mặt " thành "sữarửamặt"
                def simplify_name(text):
                    return "".join(str(text).split()).lower()
                
                excel_simplified = simplify_name(name_excel)
                
                matched_product = None
                for p in all_products:
                    # Rút gọn luôn tên trong Database để so sánh 2 bên
                    if simplify_name(p.name) == excel_simplified:
                        matched_product = p
                        break
                
                if matched_product:
                    # NẾU ĐÃ TỒN TẠI -> Cập nhật số lượng & Giá
                    matched_product.stock = (matched_product.stock or 0) + stock
                    matched_product.price = price
                    if original_price:
                        matched_product.original_price = original_price
                        
                    matched_product.save()
                    count_update += 1
                else:
                    # NẾU CHƯA CÓ -> Tạo mới
                    new_product = Product.objects.create(
                        name=name_excel, # Vẫn lưu tên chuẩn đẹp từ Excel
                        price=price,
                        original_price=original_price,
                        stock=stock,
                        category=category,
                        image_url=str(row.get('Link ảnh', '')).strip(),
                        description=str(row.get('Mô tả', '')).strip()
                    )
                    # Thêm luôn vào danh sách tạm để lỡ file Excel có 2 dòng giống nhau nó sẽ tự động cập nhật chứ k tạo thêm
                    all_products.append(new_product)
                    count_new += 1
                    
            messages.success(request, f"✅ Báo cáo: Đã tạo mới {count_new} SP và Cộng dồn số lượng cho {count_update} SP cũ!")
            
        except Exception as e:
            messages.error(request, f"❌ Lỗi khi xử lý file: {str(e)}")
            
    return redirect('dashboard')