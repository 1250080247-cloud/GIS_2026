# 📘 HƯỚNG DẪN CÀI ĐẶT VÀ CHẠY PROJECT — MyCosmeticsStore

> **Project:** MyCosmeticsStore — Hệ thống quản lý cửa hàng mỹ phẩm  
> **Framework:** Django 6.0.1  
> **Database:** PostgreSQL  
> **Ngôn ngữ:** Python  

---

## 📑 Mục lục

1. [Yêu cầu hệ thống](#1-yêu-cầu-hệ-thống)
2. [Cài đặt phần mềm cần thiết](#2-cài-đặt-phần-mềm-cần-thiết)
3. [Cấu hình PostgreSQL](#3-cấu-hình-postgresql)
4. [Tải và mở Project](#4-tải-và-mở-project)
5. [Tạo môi trường ảo (Virtual Environment)](#5-tạo-môi-trường-ảo-virtual-environment)
6. [Cài đặt thư viện (Dependencies)](#6-cài-đặt-thư-viện-dependencies)
7. [Cấu hình Database](#7-cấu-hình-database)
8. [Chạy Migrations](#8-chạy-migrations)
9. [Tạo tài khoản Admin](#9-tạo-tài-khoản-admin)
10. [Chạy Server](#10-chạy-server)
11. [Truy cập ứng dụng](#11-truy-cập-ứng-dụng)
12. [Cấu trúc Project](#12-cấu-trúc-project)
13. [Các tính năng chính](#13-các-tính-năng-chính)
14. [Xử lý lỗi thường gặp](#14-xử-lý-lỗi-thường-gặp)

---

## 1. Yêu cầu hệ thống

| Thành phần       | Yêu cầu tối thiểu                |
|------------------|-----------------------------------|
| Hệ điều hành     | Windows 10/11, macOS, hoặc Linux |
| Python           | **3.10** trở lên                 |
| PostgreSQL       | **14** trở lên                   |
| pip              | Đi kèm với Python               |
| Git *(tùy chọn)* | Phiên bản mới nhất               |

---

## 2. Cài đặt phần mềm cần thiết

### 2.1. Cài đặt Python

1. Tải Python từ: [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Khi cài đặt, **bắt buộc tích chọn** ☑️ `Add Python to PATH`
3. Kiểm tra sau khi cài:

```bash
python --version
```

> Kết quả mong đợi: `Python 3.10.x` hoặc cao hơn.

### 2.2. Cài đặt PostgreSQL

1. Tải PostgreSQL từ: [https://www.postgresql.org/download/](https://www.postgresql.org/download/)
2. Trong quá trình cài đặt:
   - **Ghi nhớ mật khẩu** bạn đặt cho user `postgres` (mặc định project dùng `123456`)
   - Giữ nguyên **port mặc định** là `5432`
   - Cài đặt **pgAdmin** (đi kèm trong bộ cài) để quản lý database bằng giao diện

3. Kiểm tra sau khi cài:

```bash
psql --version
```

---

## 3. Cấu hình PostgreSQL

### 3.1. Tạo Database

Bạn cần tạo database tên `cosmetics_db`. Có **2 cách**:

#### Cách 1: Dùng dòng lệnh (Command Line)

Mở **Command Prompt** hoặc **PowerShell**, chạy:

```bash
psql -U postgres
```

Nhập mật khẩu khi được yêu cầu, sau đó chạy:

```sql
CREATE DATABASE cosmetics_db;
```

Thoát khỏi psql:

```sql
\q
```

#### Cách 2: Dùng pgAdmin (giao diện)

1. Mở **pgAdmin 4**
2. Kết nối đến server `PostgreSQL` (nhập mật khẩu `postgres`)
3. Click chuột phải vào **Databases** → **Create** → **Database...**
4. Nhập tên: `cosmetics_db`
5. Nhấn **Save**

---

## 4. Tải và mở Project

Nếu project đã có sẵn trên máy, mở thư mục project:

```bash
cd D:\MyCosmeticsStore_BU
```

Nếu project trên Git, clone về:

```bash
git clone <URL_REPO>
cd MyCosmeticsStore_BU
```

---

## 5. Tạo môi trường ảo (Virtual Environment)

> ⚠️ **Quan trọng:** Luôn sử dụng môi trường ảo để tránh xung đột thư viện giữa các project.

### Tạo mới venv (nếu chưa có thư mục `venv`):

```bash
python -m venv venv
```

### Kích hoạt venv:

**Windows (Command Prompt):**
```bash
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

> 💡 Nếu PowerShell báo lỗi **"execution policy"**, chạy lệnh sau trước:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

**macOS / Linux:**
```bash
source venv/bin/activate
```

### Dấu hiệu kích hoạt thành công:

Dòng lệnh sẽ hiển thị `(venv)` ở đầu:

```
(venv) D:\MyCosmeticsStore_BU>
```

---

## 6. Cài đặt thư viện (Dependencies)

Sau khi kích hoạt venv, cài đặt tất cả thư viện cần thiết:

```bash
pip install -r requirements.txt
```

### Danh sách thư viện sẽ được cài:

| Thư viện           | Phiên bản | Mục đích                          |
|---------------------|-----------|-----------------------------------|
| Django              | 6.0.1     | Web framework chính               |
| psycopg2-binary     | 2.9.11    | Kết nối PostgreSQL                |
| Pillow              | 12.1.0    | Xử lý hình ảnh (upload sản phẩm) |
| pandas              | 3.0.2     | Xử lý dữ liệu, import Excel     |
| openpyxl            | 3.1.5     | Đọc/ghi file Excel (.xlsx)       |
| numpy               | 2.4.4     | Thư viện tính toán                |
| sqlparse            | 0.5.5     | Phân tích SQL (Django dependency) |
| asgiref             | 3.11.0    | ASGI support cho Django           |

### Kiểm tra cài đặt thành công:

```bash
pip list
```

---

## 7. Cấu hình Database

Mở file `cosmetics_project/settings.py` và kiểm tra phần **DATABASES**:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'cosmetics_db',        # Tên database
        'USER': 'postgres',            # User PostgreSQL
        'PASSWORD': '123456',          # ⚠️ Đổi thành mật khẩu PostgreSQL của bạn
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

> ⚠️ **LƯU Ý:** Nếu mật khẩu PostgreSQL của bạn **khác** `123456`, hãy sửa giá trị `PASSWORD` cho đúng.

---

## 8. Chạy Migrations

Migration sẽ tự động tạo các bảng trong database dựa trên models đã định nghĩa.

### Bước 1: Tạo migrations (nếu có thay đổi models):

```bash
python manage.py makemigrations
```

### Bước 2: Áp dụng migrations vào database:

```bash
python manage.py migrate
```

> ✅ Kết quả mong đợi: Các dòng `Applying store.0001_initial... OK`, `Applying store.0002_...  OK`, v.v.

---

## 9. Tạo tài khoản Admin

Tạo tài khoản **superuser** để truy cập trang quản trị:

```bash
python manage.py createsuperuser
```

Nhập thông tin theo yêu cầu:

```
Username: admin
Email address: admin@example.com
Password: ********
Password (again): ********
```

> 💡 Mật khẩu không hiển thị khi gõ, đây là bình thường.

---

## 10. Chạy Server

Khởi động development server:

```bash
python manage.py runserver
```

> ✅ Kết quả mong đợi:
> ```
> Starting development server at http://127.0.0.1:8000/
> Quit the server with CTRL-BREAK.
> ```

---

## 11. Truy cập ứng dụng

Mở trình duyệt và truy cập các đường dẫn sau:

| Trang                    | URL                                         | Mô tả                           |
|--------------------------|---------------------------------------------|----------------------------------|
| 🏠 Trang chủ             | http://127.0.0.1:8000/                     | Landing page cửa hàng           |
| 🗺️ Bản đồ chi nhánh     | http://127.0.0.1:8000/map/                 | Xem vị trí các chi nhánh        |
| 🔑 Đăng nhập             | http://127.0.0.1:8000/login/               | Trang đăng nhập                  |
| 📝 Đăng ký               | http://127.0.0.1:8000/register/            | Đăng ký tài khoản mới           |
| 📊 Dashboard quản trị    | http://127.0.0.1:8000/dashboard/           | Trang quản lý (cần đăng nhập)   |
| ⚙️ Django Admin          | http://127.0.0.1:8000/admin/               | Trang admin Django               |
| 🔍 Tìm kiếm             | http://127.0.0.1:8000/search/              | Tìm kiếm sản phẩm               |
| 👤 Hồ sơ cá nhân        | http://127.0.0.1:8000/profile/             | Quản lý hồ sơ khách hàng        |

---

## 12. Cấu trúc Project

```
MyCosmeticsStore_BU/
│
├── cosmetics_project/          # ⚙️ Cấu hình chính của Django
│   ├── __init__.py
│   ├── settings.py             # Cấu hình database, email, static files
│   ├── urls.py                 # URL routing chính (chuyển hướng sang store)
│   ├── wsgi.py                 # Cấu hình WSGI (deploy production)
│   └── asgi.py                 # Cấu hình ASGI
│
├── store/                      # 🏪 App chính của cửa hàng
│   ├── models.py               # Định nghĩa database models (8 models)
│   ├── views.py                # Xử lý logic nghiệp vụ
│   ├── urls.py                 # URL routing cho app store
│   ├── forms.py                # Django Forms (ProductForm)
│   ├── admin.py                # Đăng ký models vào Django Admin
│   ├── templates/store/        # 📄 HTML Templates (22 files)
│   │   ├── base.html           #   Template gốc
│   │   ├── landing.html        #   Trang chủ
│   │   ├── dashboard.html      #   Trang quản trị
│   │   ├── product_detail.html #   Chi tiết sản phẩm
│   │   ├── login.html          #   Đăng nhập
│   │   ├── register.html       #   Đăng ký
│   │   └── ...                 #   Và nhiều template khác
│   ├── static/store/css/       # 🎨 CSS styling
│   └── migrations/             # 📦 Database migrations
│
├── media/                      # 🖼️ Thư mục chứa ảnh upload
│   ├── products/               #   Ảnh sản phẩm
│   └── branches/               #   Ảnh chi nhánh
│
├── manage.py                   # 🚀 Django CLI entry point
├── requirements.txt            # 📋 Danh sách thư viện
└── venv/                       # 🐍 Môi trường ảo Python
```

### Database Models (8 Models):

| Model            | Mô tả                                 |
|------------------|----------------------------------------|
| `UserProfile`    | Hồ sơ người dùng (vai trò, chi nhánh) |
| `Category`       | Danh mục sản phẩm                     |
| `Product`        | Sản phẩm mỹ phẩm                     |
| `CartItem`       | Giỏ hàng                              |
| `Order`          | Đơn hàng                              |
| `OrderDetail`    | Chi tiết đơn hàng                     |
| `StoreBranch`    | Chi nhánh cửa hàng                    |
| `StockTransfer`  | Xuất kho hàng                         |

### Phân quyền người dùng (4 vai trò):

| Vai trò        | Quyền hạn                              |
|----------------|----------------------------------------|
| `SUPERADMIN`   | Admin Tổng — Toàn quyền hệ thống      |
| `BRANCHADMIN`  | Admin Chi Nhánh — Quản lý chi nhánh    |
| `STAFF`        | Nhân viên cửa hàng                     |
| `CUSTOMER`     | Khách hàng — Mua sắm, đặt hàng        |

---

## 13. Các tính năng chính

### 🛒 Khách hàng
- Xem danh sách sản phẩm & chi tiết sản phẩm
- Tìm kiếm sản phẩm
- Thêm vào giỏ hàng & đặt hàng (checkout)
- Đăng ký / Đăng nhập / Đổi mật khẩu
- Quên mật khẩu (gửi email qua Mailtrap)
- Xem hồ sơ cá nhân

### 📊 Quản trị viên (Dashboard)
- Quản lý sản phẩm (Thêm / Sửa / Xóa)
- Import sản phẩm từ file Excel
- Quản lý đơn hàng & cập nhật trạng thái
- Quản lý chi nhánh cửa hàng (CRUD)
- Quản lý kho hàng & xuất kho
- Quản lý người dùng & phân quyền
- Xuất hóa đơn

### 🗺️ Bản đồ
- Hiển thị vị trí các chi nhánh trên bản đồ

---

## 14. Xử lý lỗi thường gặp

### ❌ Lỗi 1: `ModuleNotFoundError: No module named 'django'`

**Nguyên nhân:** Chưa kích hoạt môi trường ảo hoặc chưa cài thư viện.

**Giải pháp:**
```bash
# Kích hoạt venv trước
venv\Scripts\activate

# Sau đó cài lại thư viện
pip install -r requirements.txt
```

---

### ❌ Lỗi 2: `django.db.utils.OperationalError: FATAL: database "cosmetics_db" does not exist`

**Nguyên nhân:** Chưa tạo database `cosmetics_db` trong PostgreSQL.

**Giải pháp:** Tạo database theo [Bước 3](#3-cấu-hình-postgresql).

---

### ❌ Lỗi 3: `django.db.utils.OperationalError: FATAL: password authentication failed for user "postgres"`

**Nguyên nhân:** Mật khẩu PostgreSQL trong `settings.py` không đúng.

**Giải pháp:** Mở `cosmetics_project/settings.py`, sửa `PASSWORD` thành mật khẩu PostgreSQL đúng của bạn.

---

### ❌ Lỗi 4: `psycopg2.OperationalError: could not connect to server`

**Nguyên nhân:** PostgreSQL chưa chạy.

**Giải pháp:**
1. Mở **Services** (gõ `services.msc` trong Start Menu)
2. Tìm **postgresql-x64-XX** → Click chuột phải → **Start**

---

### ❌ Lỗi 5: PowerShell báo `cannot be loaded because running scripts is disabled`

**Nguyên nhân:** PowerShell chặn chạy scripts.

**Giải pháp:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### ❌ Lỗi 6: `pip` không nhận lệnh

**Nguyên nhân:** Python chưa được thêm vào PATH.

**Giải pháp:** Cài lại Python và tích chọn **"Add Python to PATH"**.

---

## ⚡ Tóm tắt nhanh — Chạy Project trong 5 bước

```bash
# 1. Mở thư mục project
cd D:\MyCosmeticsStore_BU

# 2. Kích hoạt môi trường ảo
venv\Scripts\activate

# 3. Cài thư viện (chỉ cần lần đầu)
pip install -r requirements.txt

# 4. Chạy migrations (chỉ cần lần đầu hoặc khi có thay đổi models)
python manage.py migrate

# 5. Chạy server
python manage.py runserver
```

Truy cập: **http://127.0.0.1:8000/** 🎉

---

## 📧 Cấu hình Email (Mailtrap)

Project sử dụng **Mailtrap** để test chức năng gửi email (quên mật khẩu). Cấu hình nằm trong `settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'sandbox.smtp.mailtrap.io'
EMAIL_HOST_USER = 'e4effb6b5746c1'
EMAIL_HOST_PASSWORD = '9bc2717cc6cd1b'
EMAIL_PORT = '2525'
```

> 💡 Để xem email test, đăng nhập vào [Mailtrap](https://mailtrap.io/) với tài khoản tương ứng.

---

> 📝 *Tài liệu này được tạo tự động dựa trên phân tích mã nguồn project MyCosmeticsStore.*
