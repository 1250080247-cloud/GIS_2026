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
    path('dashboard/create-user/', views.create_internal_user, name='create_internal_user'),
    path('dashboard/user/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('search/', views.search_results, name='search'),
    path('dashboard/import-excel/', views.import_products_excel, name='import_products_excel'),
    path('dashboard/user/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('profile/', views.customer_profile, name='customer_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),

# ... (các url khác) ...

path('password_reset/', auth_views.PasswordResetView.as_view(
    template_name='store/password_reset_form.html'
), name='password_reset'),

path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
    template_name='store/password_reset_done.html'
), name='password_reset_done'),

path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
    template_name='store/password_reset_confirm.html'
), name='password_reset_confirm'),

path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
    template_name='store/password_reset_complete.html'
), name='password_reset_complete'),
]