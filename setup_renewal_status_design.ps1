$ErrorActionPreference = "Stop"

Write-Host "Creating Renewal Status platform files..." -ForegroundColor Cyan

$path = "config\settings.py"
$dir = Split-Path $path -Parent
if ($dir -and !(Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
@'
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-renewal-status-local-dev-key"
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "inquiry",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ar-sa"
TIME_ZONE = "Asia/Riyadh"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

'@ | Set-Content -Path $path -Encoding UTF8
Write-Host "✓ config\settings.py"

$path = "config\urls.py"
$dir = Split-Path $path -Parent
if ($dir -and !(Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
@'
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("inquiry.urls")),
]

'@ | Set-Content -Path $path -Encoding UTF8
Write-Host "✓ config\urls.py"

$path = "inquiry\models.py"
$dir = Split-Path $path -Parent
if ($dir -and !(Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
@'
from django.db import models


class RenewalRecord(models.Model):
    STATUS_RENEWED = "renewed"
    STATUS_NOT_RENEWED = "not_renewed"
    STATUS_LIMITED = "limited"
    STATUS_PENDING = "pending"

    STATUS_CHOICES = [
        (STATUS_RENEWED, "تم التجديد"),
        (STATUS_NOT_RENEWED, "لم يتم التجديد"),
        (STATUS_LIMITED, "تم التجديد لمدة محددة"),
        (STATUS_PENDING, "تحت الإجراء"),
    ]

    national_id = models.CharField("السجل المدني", max_length=20, unique=True, db_index=True)
    full_name = models.CharField("الاسم الرباعي", max_length=255)
    school_name = models.CharField("اسم المدرسة", max_length=255, blank=True)
    sector = models.CharField("القطاع التعليمي", max_length=150, blank=True)
    category = models.CharField("الفئة", max_length=100, blank=True)
    raw_status = models.CharField("الحالة الأصلية", max_length=255, blank=True)
    status_code = models.CharField("تصنيف الحالة", max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING)
    note = models.TextField("ملاحظة", blank=True)
    is_published = models.BooleanField("منشور", default=True)
    created_at = models.DateTimeField("تاريخ الإنشاء", auto_now_add=True)
    updated_at = models.DateTimeField("آخر تحديث", auto_now=True)

    class Meta:
        verbose_name = "سجل استعلام"
        verbose_name_plural = "سجلات الاستعلام"
        ordering = ["category", "sector", "full_name"]

    def __str__(self):
        return f"{self.full_name} - {self.national_id}"

    @property
    def status_label(self):
        return dict(self.STATUS_CHOICES).get(self.status_code, "تحت الإجراء")

    @property
    def status_css(self):
        return {
            self.STATUS_RENEWED: "renewed",
            self.STATUS_NOT_RENEWED: "not-renewed",
            self.STATUS_LIMITED: "limited",
            self.STATUS_PENDING: "pending",
        }.get(self.status_code, "pending")

    @property
    def status_message(self):
        if self.status_code == self.STATUS_RENEWED:
            return "نبارك لكم تجديد التكليف، سائلين الله لكم التوفيق والسداد."
        if self.status_code == self.STATUS_NOT_RENEWED:
            return "لم يتم التجديد وفق البيانات المعتمدة لدى قسم الإدارة المدرسية."
        if self.status_code == self.STATUS_LIMITED:
            return "تم التجديد لمدة محددة وفق البيانات المعتمدة لدى قسم الإدارة المدرسية."
        return "حالة الطلب تحت الإجراء أو مرفوعة لصاحب الصلاحية."


class InquiryLog(models.Model):
    national_id = models.CharField("السجل المستعلم عنه", max_length=20, db_index=True)
    found = models.BooleanField("تم العثور على نتيجة", default=False)
    created_at = models.DateTimeField("وقت الاستعلام", auto_now_add=True)
    ip_address = models.GenericIPAddressField("IP", null=True, blank=True)

    class Meta:
        verbose_name = "سجل عملية استعلام"
        verbose_name_plural = "سجل عمليات الاستعلام"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.national_id} - {'وجد' if self.found else 'لم يجد'}"

'@ | Set-Content -Path $path -Encoding UTF8
Write-Host "✓ inquiry\models.py"

$path = "inquiry\admin.py"
$dir = Split-Path $path -Parent
if ($dir -and !(Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
@'
from django.contrib import admin
from .models import InquiryLog, RenewalRecord


@admin.register(RenewalRecord)
class RenewalRecordAdmin(admin.ModelAdmin):
    list_display = ("full_name", "national_id", "category", "school_name", "sector", "status_code", "is_published")
    list_filter = ("status_code", "category", "sector", "is_published")
    search_fields = ("full_name", "national_id", "school_name", "sector", "category", "raw_status")
    list_editable = ("is_published",)
    ordering = ("category", "sector", "full_name")


@admin.register(InquiryLog)
class InquiryLogAdmin(admin.ModelAdmin):
    list_display = ("national_id", "found", "created_at", "ip_address")
    list_filter = ("found", "created_at")
    search_fields = ("national_id", "ip_address")
    readonly_fields = ("national_id", "found", "created_at", "ip_address")

'@ | Set-Content -Path $path -Encoding UTF8
Write-Host "✓ inquiry\admin.py"

$path = "inquiry\urls.py"
$dir = Split-Path $path -Parent
if ($dir -and !(Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
@'
from django.urls import path
from . import views

app_name = "inquiry"

urlpatterns = [
    path("", views.home, name="home"),
]

'@ | Set-Content -Path $path -Encoding UTF8
Write-Host "✓ inquiry\urls.py"

$path = "inquiry\views.py"
$dir = Split-Path $path -Parent
if ($dir -and !(Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
@'
import re
from django.shortcuts import render
from .models import InquiryLog, RenewalRecord


def normalize_national_id(value: str) -> str:
    value = str(value or "").strip()
    value = value.replace(".0", "")
    return re.sub(r"\D", "", value)


def get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def home(request):
    context = {}

    if request.method == "POST":
        national_id = normalize_national_id(request.POST.get("national_id"))
        context["searched"] = True
        context["national_id"] = national_id

        if not national_id:
            context["error"] = "فضلاً أدخل السجل المدني."
            return render(request, "inquiry/home.html", context)

        record = RenewalRecord.objects.filter(
            national_id=national_id,
            is_published=True,
        ).first()

        InquiryLog.objects.create(
            national_id=national_id,
            found=bool(record),
            ip_address=get_client_ip(request),
        )

        if record:
            context["record"] = record
        else:
            context["not_found"] = True

    return render(request, "inquiry/home.html", context)

'@ | Set-Content -Path $path -Encoding UTF8
Write-Host "✓ inquiry\views.py"

$path = "static\inquiry\style.css"
$dir = Split-Path $path -Parent
if ($dir -and !(Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
@'
:root{
  --bg:#eef4f6;
  --card:#ffffff;
  --ink:#17333a;
  --muted:#6a7d83;
  --border:#dfe9ec;
  --primary:#1f6f7c;
  --primary-dark:#144e58;
  --soft:#f7fbfc;
  --shadow:0 28px 80px rgba(23,51,58,.13);
  --green:#158460;
  --green-bg:#ecf8f3;
  --red:#b44545;
  --red-bg:#fff1f1;
  --gold:#a87517;
  --gold-bg:#fff8e8;
  --blue:#276f91;
  --blue-bg:#edf7fb;
}

*{box-sizing:border-box}

body{
  margin:0;
  min-height:100vh;
  font-family:"Cairo","Segoe UI",Tahoma,Arial,sans-serif;
  color:var(--ink);
  background:
    radial-gradient(circle at top right, rgba(31,111,124,.16), transparent 34rem),
    radial-gradient(circle at bottom left, rgba(168,117,23,.10), transparent 30rem),
    linear-gradient(135deg,#f7fafb 0%,var(--bg) 100%);
}

body::before{
  content:"";
  position:fixed;
  inset:0;
  pointer-events:none;
  background-image:
    linear-gradient(rgba(23,51,58,.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(23,51,58,.035) 1px, transparent 1px);
  background-size:34px 34px;
  mask-image:linear-gradient(to bottom, rgba(0,0,0,.6), transparent 72%);
}

.page-shell{
  position:relative;
  z-index:1;
  width:min(940px,calc(100% - 32px));
  margin:0 auto;
  padding:56px 0 28px;
}

.hero-card,
.result-card{
  background:rgba(255,255,255,.88);
  border:1px solid rgba(223,233,236,.9);
  border-radius:34px;
  box-shadow:var(--shadow);
  backdrop-filter:blur(18px);
}

.hero-card{
  padding:34px;
  overflow:hidden;
  position:relative;
}

.hero-card::after{
  content:"";
  position:absolute;
  top:-120px;
  left:-120px;
  width:270px;
  height:270px;
  border-radius:50%;
  background:linear-gradient(145deg,rgba(31,111,124,.18),rgba(31,111,124,0));
}

.brand-row{
  display:flex;
  align-items:center;
  gap:16px;
  position:relative;
  z-index:1;
}

.brand-mark{
  width:62px;
  height:62px;
  border-radius:22px;
  display:grid;
  place-items:center;
  color:#fff;
  font-weight:800;
  font-size:26px;
  background:linear-gradient(135deg,var(--primary),var(--primary-dark));
  box-shadow:0 16px 36px rgba(31,111,124,.27);
}

.eyebrow{
  margin:0 0 4px;
  color:var(--primary);
  font-weight:700;
  letter-spacing:-.2px;
}

h1{
  margin:0;
  font-size:clamp(28px,4vw,44px);
  line-height:1.25;
  letter-spacing:-1px;
}

.subtitle{
  margin:22px 0 0;
  max-width:760px;
  color:var(--muted);
  font-size:16px;
  line-height:1.9;
}

.search-form{
  margin-top:30px;
  padding:18px;
  border-radius:26px;
  background:var(--soft);
  border:1px solid var(--border);
}

.search-form label{
  display:block;
  margin:0 2px 10px;
  font-size:14px;
  color:var(--muted);
  font-weight:700;
}

.input-row{
  display:flex;
  gap:12px;
}

input{
  flex:1;
  height:58px;
  border:1px solid var(--border);
  border-radius:18px;
  padding:0 18px;
  color:var(--ink);
  background:#fff;
  outline:none;
  font:700 18px/1 "Cairo",sans-serif;
  transition:.2s ease;
}

input:focus{
  border-color:rgba(31,111,124,.65);
  box-shadow:0 0 0 5px rgba(31,111,124,.09);
}

button{
  height:58px;
  min-width:145px;
  border:0;
  border-radius:18px;
  color:#fff;
  cursor:pointer;
  font:800 16px/1 "Cairo",sans-serif;
  background:linear-gradient(135deg,var(--primary),var(--primary-dark));
  box-shadow:0 18px 34px rgba(31,111,124,.22);
  transition:.2s ease;
}

button:hover{
  transform:translateY(-1px);
  box-shadow:0 22px 38px rgba(31,111,124,.26);
}

.alert{
  margin-top:12px;
  padding:12px 14px;
  border-radius:16px;
  font-weight:700;
}

.alert.error{
  color:var(--red);
  background:var(--red-bg);
}

.result-card{
  margin-top:22px;
  padding:28px;
  position:relative;
  overflow:hidden;
}

.result-card::before{
  content:"";
  position:absolute;
  inset:0 auto 0 0;
  width:8px;
  background:var(--primary);
}

.status-head{
  display:flex;
  align-items:center;
  gap:14px;
}

.status-head p{
  margin:0 0 4px;
  color:var(--muted);
  font-weight:700;
  font-size:14px;
}

.status-head h2{
  margin:0;
  font-size:32px;
  letter-spacing:-.6px;
}

.status-icon{
  width:58px;
  height:58px;
  border-radius:20px;
  display:grid;
  place-items:center;
  background:var(--blue-bg);
  color:var(--blue);
}

.status-icon::after{
  content:"";
  width:20px;
  height:20px;
  border-radius:50%;
  background:currentColor;
  box-shadow:0 0 0 8px color-mix(in srgb, currentColor 15%, transparent);
}

.status-message{
  margin:20px 0 0;
  padding:18px 20px;
  border-radius:22px;
  background:var(--soft);
  color:#435c63;
  font-weight:700;
  line-height:1.9;
}

.info-grid{
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  gap:14px;
  margin-top:18px;
}

.info-item{
  padding:16px;
  border:1px solid var(--border);
  border-radius:22px;
  background:#fff;
}

.info-item span{
  display:block;
  margin-bottom:5px;
  color:var(--muted);
  font-size:13px;
  font-weight:700;
}

.info-item strong{
  display:block;
  color:var(--ink);
  font-size:16px;
  line-height:1.6;
}

.official-note{
  margin-top:16px;
  padding:14px 16px;
  border-radius:18px;
  color:var(--muted);
  background:#fbfdfd;
  border:1px dashed var(--border);
  font-size:13px;
  font-weight:700;
}

.status-renewed::before{background:var(--green)}
.status-renewed .status-icon{background:var(--green-bg);color:var(--green)}
.status-renewed .status-head h2{color:var(--green)}

.status-not-renewed::before{background:var(--red)}
.status-not-renewed .status-icon{background:var(--red-bg);color:var(--red)}
.status-not-renewed .status-head h2{color:var(--red)}

.status-limited::before{background:var(--blue)}
.status-limited .status-icon{background:var(--blue-bg);color:var(--blue)}
.status-limited .status-head h2{color:var(--blue)}

.status-pending::before{background:var(--gold)}
.status-pending .status-icon{background:var(--gold-bg);color:var(--gold)}
.status-pending .status-head h2{color:var(--gold)}

.status-missing::before{background:#7a8990}
.status-missing .status-icon{background:#eef2f3;color:#7a8990}
.status-missing .status-head h2{color:#52656c}

.page-footer{
  margin-top:22px;
  text-align:center;
  color:#6f8288;
  font-size:13px;
  font-weight:700;
}

@media (max-width:720px){
  .page-shell{width:min(100% - 20px,940px);padding-top:20px}
  .hero-card,.result-card{border-radius:26px;padding:22px}
  .brand-row{align-items:flex-start}
  .brand-mark{width:52px;height:52px;border-radius:18px;font-size:22px}
  .input-row{flex-direction:column}
  button{width:100%}
  .info-grid{grid-template-columns:1fr}
  .status-head h2{font-size:26px}
}

'@ | Set-Content -Path $path -Encoding UTF8
Write-Host "✓ static\inquiry\style.css"

$path = "templates\inquiry\home.html"
$dir = Split-Path $path -Parent
if ($dir -and !(Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
@'
{% load static %}
<!doctype html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>استعلام حالة التكليف</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{% static 'inquiry/style.css' %}">
</head>
<body>
  <main class="page-shell">
    <section class="hero-card">
      <div class="brand-row">
        <div class="brand-mark">ع</div>
        <div>
          <p class="eyebrow">الإدارة العامة للتعليم بمنطقة عسير</p>
          <h1>استعلام حالة التكليف</h1>
        </div>
      </div>

      <p class="subtitle">
        خدمة مخصصة للاستعلام عن حالة التكليف للتشكيلات المدرسية وفق البيانات المعتمدة لدى قسم الإدارة المدرسية.
      </p>

      <form class="search-form" method="post" autocomplete="off">
        {% csrf_token %}
        <label for="national_id">السجل المدني</label>
        <div class="input-row">
          <input
            id="national_id"
            name="national_id"
            type="text"
            inputmode="numeric"
            placeholder="أدخل السجل المدني"
            value="{{ national_id|default:'' }}"
            maxlength="20"
            autofocus
          >
          <button type="submit">استعلام</button>
        </div>
        {% if error %}
          <div class="alert error">{{ error }}</div>
        {% endif %}
      </form>
    </section>

    {% if record %}
      <section class="result-card status-{{ record.status_css }}">
        <div class="status-head">
          <div class="status-icon"></div>
          <div>
            <p>حالة التكليف</p>
            <h2>{{ record.status_label }}</h2>
          </div>
        </div>

        <p class="status-message">{{ record.status_message }}</p>

        <div class="info-grid">
          <div class="info-item">
            <span>الاسم</span>
            <strong>{{ record.full_name }}</strong>
          </div>
          <div class="info-item">
            <span>الفئة</span>
            <strong>{{ record.category|default:'غير متوفر' }}</strong>
          </div>
          <div class="info-item">
            <span>المدرسة</span>
            <strong>{{ record.school_name|default:'غير متوفر' }}</strong>
          </div>
          <div class="info-item">
            <span>القطاع التعليمي</span>
            <strong>{{ record.sector|default:'غير متوفر' }}</strong>
          </div>
        </div>

        <div class="official-note">
          هذه النتيجة لغرض الاستعلام فقط، وتعتمد على البيانات المنشورة في النظام.
        </div>
      </section>
    {% elif not_found %}
      <section class="result-card status-missing">
        <div class="status-head">
          <div class="status-icon"></div>
          <div>
            <p>نتيجة الاستعلام</p>
            <h2>لا توجد نتيجة</h2>
          </div>
        </div>
        <p class="status-message">
          لم يتم العثور على بيانات منشورة مرتبطة بالسجل المدني المدخل. يرجى التأكد من الرقم والمحاولة مرة أخرى.
        </p>
      </section>
    {% endif %}

    <footer class="page-footer">
      قسم الإدارة المدرسية — خدمة الاستعلام الرقمية
    </footer>
  </main>
</body>
</html>

'@ | Set-Content -Path $path -Encoding UTF8
Write-Host "✓ templates\inquiry\home.html"

$path = "inquiry\management\commands\import_renewal_excel.py"
$dir = Split-Path $path -Parent
if ($dir -and !(Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
@'
import re
from pathlib import Path

import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from inquiry.models import RenewalRecord


def clean_value(value):
    if pd.isna(value):
        return ""
    value = str(value).strip()
    if value.endswith(".0"):
        value = value[:-2]
    return value


def clean_national_id(value):
    return re.sub(r"\D", "", clean_value(value))


def normalize_header(value):
    value = clean_value(value)
    value = value.replace("ـ", "")
    return re.sub(r"\s+", " ", value).strip()


def pick_column(columns, choices):
    normalized = {normalize_header(c): c for c in columns}
    for choice in choices:
        if choice in normalized:
            return normalized[choice]
    for col in columns:
        h = normalize_header(col)
        if any(choice in h for choice in choices):
            return col
    return None


def classify_status(raw_status):
    text = clean_value(raw_status).replace(" ", "")
    if any(word in text for word in ["لايجدد", "لميتجديد", "عدمتجديد", "لايتمالتجديد", "لمتمالتجديد"]):
        return RenewalRecord.STATUS_NOT_RENEWED
    if "يجددإلى" in text or "يجددالى" in text or "مدةمحددة" in text:
        return RenewalRecord.STATUS_LIMITED
    if "صلاحية" in text or "مرفوع" in text or "تحتالإجراء" in text or "تحتالاجراء" in text:
        return RenewalRecord.STATUS_PENDING
    if "تجديد" in text or "مجدد" in text or "تمالتجديد" in text:
        return RenewalRecord.STATUS_RENEWED
    return RenewalRecord.STATUS_PENDING


class Command(BaseCommand):
    help = "Import renewal inquiry records from Excel."

    def add_arguments(self, parser):
        parser.add_argument("excel_path", type=str, help="Path to the Excel file")
        parser.add_argument("--clear", action="store_true", help="Delete existing records before import")

    def handle(self, *args, **options):
        path = Path(options["excel_path"])
        if not path.exists():
            raise CommandError(f"Excel file not found: {path}")

        if options["clear"]:
            RenewalRecord.objects.all().delete()

        df = pd.read_excel(path, dtype=str)
        df.columns = [normalize_header(c) for c in df.columns]

        national_col = pick_column(df.columns, ["السجل المدني", "السجل", "الهوية الوطنية", "رقم الهوية", "رقم السجل"])
        name_col = pick_column(df.columns, ["الاسم الرباعي", "الاسم", "اسم الموظف", "اسم المستفيد"])
        school_col = pick_column(df.columns, ["اسم المدرسة", "المدرسة"])
        sector_col = pick_column(df.columns, ["القطاع التعليمي", "القطاع"])
        category_col = pick_column(df.columns, ["الفئة", "العمل الحالي", "المسمى"])
        status_col = pick_column(df.columns, ["الحالة", "الحلة", "حالة التجديد", "التوصية"])

        missing = []
        if not national_col:
            missing.append("السجل المدني")
        if not name_col:
            missing.append("الاسم")
        if not status_col:
            missing.append("الحالة")
        if missing:
            raise CommandError("الأعمدة المفقودة: " + "، ".join(missing))

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for _, row in df.iterrows():
            national_id = clean_national_id(row.get(national_col))
            full_name = clean_value(row.get(name_col))

            if not national_id or not full_name:
                skipped_count += 1
                continue

            raw_status = clean_value(row.get(status_col))
            defaults = {
                "full_name": full_name,
                "school_name": clean_value(row.get(school_col)) if school_col else "",
                "sector": clean_value(row.get(sector_col)) if sector_col else "",
                "category": clean_value(row.get(category_col)) if category_col else "",
                "raw_status": raw_status,
                "status_code": classify_status(raw_status),
                "is_published": True,
            }

            _, created = RenewalRecord.objects.update_or_create(
                national_id=national_id,
                defaults=defaults,
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS("تم الاستيراد بنجاح"))
        self.stdout.write(f"جديد: {created_count}")
        self.stdout.write(f"محدث: {updated_count}")
        self.stdout.write(f"متجاوز: {skipped_count}")

'@ | Set-Content -Path $path -Encoding UTF8
Write-Host "✓ inquiry\management\commands\import_renewal_excel.py"

if (!(Test-Path "uploads")) { New-Item -ItemType Directory -Path "uploads" -Force | Out-Null }
Write-Host "Done. Next: copy your Excel file into uploads, then run migrations and import." -ForegroundColor Green