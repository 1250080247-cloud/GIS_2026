from django.contrib import admin
from django.urls import path
from . import views  
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.landing_page, name='landing'),
    path('map/', views.home, name='map_page'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('login/', auth_views.LoginView.as_view(template_name='store/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='landing'), name='logout'),
    path('register/', views.register_user, name='register'),
    path('dashboard/', views.custom_dashboard, name='dashboard'),
    path('dashboard/inventory/', views.inventory_management, name='inventory'),
    path('dashboard/inventory/invoice/<int:transfer_id>/', views.export_invoice, name='export_invoice'),
    path('dashboard/order/<int:order_id>/invoice/', views.order_invoice, name='order_invoice'),
    path('checkout-cart/', views.checkout_cart, name='checkout_cart'),
    path('dashboard/order/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    path('dashboard/add-product/', views.add_product, name='add_product'),
    path('dashboard/add-branch/', views.add_branch, name='add_branch'),
    path('dashboard/edit-branch/<int:branch_id>/', views.edit_branch, name='edit_branch'),
    path('dashboard/delete-branch/<int:branch_id>/', views.delete_branch, name='delete_branch'),
    path('dashboard/edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('dashboard/delete/<int:product_id>/', views.delete_product, name='delete_product'),
]