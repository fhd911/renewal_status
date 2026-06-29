from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ExcelImportForm, InquirySettingsForm, RenewalRecordForm
from .models import InquiryLog, InquirySettings, RenewalRecord
from .utils import (
    CATEGORY_ACTIVITY,
    CATEGORY_COUNSELOR,
    CATEGORY_DEPUTY,
    CATEGORY_MANAGER,
    CATEGORY_UNKNOWN,
    category_label_from_key,
    normalize_national_id,
    read_excel_records,
)


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def make_reference_number(log_id):
    return f"1448-{int(log_id):06d}"




def get_inquiry_settings():
    return InquirySettings.get_solo()


def create_inquiry_log(request, national_id, records):
    first_record = records[0] if records else None

    log = InquiryLog.objects.create(
        national_id=national_id,
        mobile_last4="",
        found=bool(records),
        result_name=first_record.full_name if first_record else "",
        result_category=first_record.category if first_record else "",
        result_school=first_record.school_name if first_record else "",
        result_sector=first_record.sector if first_record else "",
        result_status_label=first_record.status_label if first_record else "",
        result_raw_status=first_record.raw_status if first_record else "",
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:1000],
    )
    log.reference_number = make_reference_number(log.id)
    log.save(update_fields=["reference_number"])
    return log


def home(request):
    settings_obj = get_inquiry_settings()
    inquiry_available = settings_obj.is_available()

    context = {
        "searched": False,
        "national_id": "",
        "records": [],
        "error": "",
        "inquiry_reference": "",
        "inquiry_settings": settings_obj,
        "inquiry_available": inquiry_available,
        "inquiry_closed_message": settings_obj.public_closed_message(),
        "inquiry_closed_reason": settings_obj.availability_reason(),
    }

    if request.method == "POST":
        if not inquiry_available:
            return render(request, "inquiry/home.html", context)

        national_id = normalize_national_id(request.POST.get("national_id"))

        context["searched"] = True
        context["national_id"] = national_id

        if not national_id:
            context["error"] = "فضلاً أدخل السجل المدني."
            return render(request, "inquiry/home.html", context)

        records = list(
            RenewalRecord.objects.filter(
                national_id=national_id,
                is_published=True,
            ).order_by("category", "school_name")
        )

        log = create_inquiry_log(request, national_id, records)
        context["inquiry_reference"] = log.reference_number

        if records:
            context["records"] = records
        else:
            context["error"] = "لا توجد بيانات مرتبطة بالسجل المدني المدخل ضمن حالات التكليف أو النقل أو التجديد لهذه المرحلة."

    return render(request, "inquiry/home.html", context)


def category_filter_q(category_key):
    mapping = {
        "manager": Q(category=CATEGORY_MANAGER) | Q(category__icontains="مدير") | Q(current_work__icontains="مدير"),
        "deputy": Q(category=CATEGORY_DEPUTY) | Q(category__icontains="وكيل") | Q(current_work__icontains="وكيل"),
        "counselor": Q(category=CATEGORY_COUNSELOR) | Q(category__icontains="موجه") | Q(category__icontains="مرشد") | Q(current_work__icontains="موجه") | Q(current_work__icontains="مرشد"),
        "activity_leader": Q(category=CATEGORY_ACTIVITY) | Q(category__icontains="رائد") | Q(category__icontains="نشاط") | Q(current_work__icontains="رائد") | Q(current_work__icontains="نشاط"),
        "unknown": Q(category="") | Q(category=CATEGORY_UNKNOWN) | Q(category__isnull=True),
    }
    return mapping.get(category_key)


def category_count(category_key):
    query = category_filter_q(category_key)
    if not query:
        return 0
    return RenewalRecord.objects.filter(query).count()


def category_status_count(category_key, status_key):
    query = category_filter_q(category_key)
    if not query:
        return 0
    return RenewalRecord.objects.filter(query, status_key=status_key).count()


def build_category_status_rows():
    categories = [
        ("manager", "مدير مدرسة"),
        ("deputy", "وكيل مدرسة"),
        ("counselor", "موجه طلابي"),
        ("activity_leader", "رائد نشاط"),
    ]

    rows = []
    for key, label in categories:
        rows.append({
            "key": key,
            "label": label,
            "total": category_count(key),
            "renewed": category_status_count(key, "renewed"),
            "not_renewed": category_status_count(key, "not_renewed"),
            "limited": category_status_count(key, "limited"),
            "pending": category_status_count(key, "pending"),
        })
    return rows


def build_admin_stats():
    return {
        "total": RenewalRecord.objects.count(),
        "published": RenewalRecord.objects.filter(is_published=True).count(),
        "renewed": RenewalRecord.objects.filter(status_key="renewed").count(),
        "not_renewed": RenewalRecord.objects.filter(status_key="not_renewed").count(),
        "limited": RenewalRecord.objects.filter(status_key="limited").count(),
        "pending": RenewalRecord.objects.filter(status_key="pending").count(),
        "manager": category_count("manager"),
        "deputy": category_count("deputy"),
        "counselor": category_count("counselor"),
        "activity_leader": category_count("activity_leader"),
        "unknown_category": category_count("unknown"),
        "inquiry_available": get_inquiry_settings().is_available(),
        "inquiry_reason": get_inquiry_settings().availability_reason(),
    }


@staff_member_required(login_url="/admin/login/")
def manage_records(request):
    query = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "").strip()
    category = (request.GET.get("category") or "").strip()

    records = RenewalRecord.objects.all().order_by("full_name", "school_name")

    if query:
        records = records.filter(
            Q(national_id__icontains=query)
            | Q(full_name__icontains=query)
            | Q(ministry_number__icontains=query)
            | Q(school_name__icontains=query)
            | Q(sector__icontains=query)
            | Q(category__icontains=query)
            | Q(current_work__icontains=query)
            | Q(raw_status__icontains=query)
            | Q(status_label__icontains=query)
        )

    if status:
        records = records.filter(status_key=status)

    category_query = category_filter_q(category)
    if category_query:
        records = records.filter(category_query)

    paginator = Paginator(records, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "query": query,
        "status": status,
        "category": category,
        "stats": build_admin_stats(),
        "category_rows": build_category_status_rows(),
        "category_label": category_label_from_key(category) if category else "",
        "inquiry_settings": get_inquiry_settings(),
    }
    return render(request, "inquiry/manage_records.html", context)


@staff_member_required(login_url="/admin/login/")
def record_create(request):
    if request.method == "POST":
        form = RenewalRecordForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "تمت إضافة السجل بنجاح.")
            return redirect("inquiry:manage_records")
    else:
        form = RenewalRecordForm()

    return render(
        request,
        "inquiry/record_form.html",
        {
            "form": form,
            "title": "إضافة مستفيد",
            "submit_label": "حفظ السجل",
        },
    )


@staff_member_required(login_url="/admin/login/")
def record_update(request, pk):
    record = get_object_or_404(RenewalRecord, pk=pk)

    if request.method == "POST":
        form = RenewalRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, "تم تحديث السجل بنجاح.")
            return redirect("inquiry:manage_records")
    else:
        form = RenewalRecordForm(instance=record)

    return render(
        request,
        "inquiry/record_form.html",
        {
            "form": form,
            "record": record,
            "title": "تعديل بيانات المستفيد",
            "submit_label": "حفظ التعديل",
        },
    )


@staff_member_required(login_url="/admin/login/")
def record_delete(request, pk):
    record = get_object_or_404(RenewalRecord, pk=pk)

    if request.method == "POST":
        record.delete()
        messages.success(request, "تم حذف السجل بنجاح.")
        return redirect("inquiry:manage_records")

    return redirect("inquiry:manage_records")


def save_uploaded_import_file(uploaded_file):
    import_dir = Path(settings.BASE_DIR) / "uploads" / "imports"
    import_dir.mkdir(parents=True, exist_ok=True)
    storage = FileSystemStorage(location=import_dir)
    safe_name = f"renewal_import_{uuid4().hex}.xlsx"
    filename = storage.save(safe_name, uploaded_file)
    return str(import_dir / filename)


def apply_excel_import(file_path, mode):
    parsed = read_excel_records(file_path)

    if mode == "replace":
        RenewalRecord.objects.all().delete()

    created = 0
    updated = 0

    for item in parsed["rows"]:
        data = {
            "mobile_last4": item.get("mobile_last4", ""),
            "full_name": item["full_name"],
            "ministry_number": item.get("ministry_number", ""),
            "school_name": item["school_name"],
            "sector": item["sector"],
            "gender": item.get("gender", ""),
            "current_work": item.get("current_work", item.get("category", "")),
            "category": item["category"],
            "raw_status": item["raw_status"],
            "status_key": item["status_key"],
            "status_label": item["status_label"],
            "status_message": item["status_message"],
            "non_renewal_reason": item.get("non_renewal_reason", ""),
            "admin_note": item.get("admin_note", ""),
            "is_published": True,
        }

        if mode == "update":
            record = RenewalRecord.objects.filter(national_id=item["national_id"]).first()
            if record:
                for key, value in data.items():
                    setattr(record, key, value)
                record.save()
                updated += 1
            else:
                RenewalRecord.objects.create(national_id=item["national_id"], **data)
                created += 1
        else:
            RenewalRecord.objects.create(national_id=item["national_id"], **data)
            created += 1

    return {
        "created": created,
        "updated": updated,
        "skipped": parsed["invalid_count"],
        "duplicates": parsed["duplicate_count"],
        "valid": parsed["valid_count"],
    }


@staff_member_required(login_url="/admin/login/")
def import_excel(request):
    form = ExcelImportForm()
    preview = None
    mode = request.session.get("renewal_import_mode", "replace")

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "preview":
            form = ExcelImportForm(request.POST, request.FILES)
            if form.is_valid():
                file_path = save_uploaded_import_file(form.cleaned_data["file"])
                preview = read_excel_records(file_path)
                request.session["renewal_import_file"] = file_path
                request.session["renewal_import_mode"] = form.cleaned_data["mode"]
                request.session.modified = True
                mode = form.cleaned_data["mode"]

        elif action == "confirm":
            file_path = request.session.get("renewal_import_file")
            mode = request.session.get("renewal_import_mode", "replace")
            confirm_import = request.POST.get("confirm_import")

            if confirm_import != "yes":
                messages.error(request, "يلزم تأكيد اعتماد الملف قبل تنفيذ الاستيراد.")
                return redirect("inquiry:import_excel")

            if not file_path or not Path(file_path).exists():
                messages.error(request, "لم يتم العثور على ملف الاستيراد. فضلاً ارفع الملف مرة أخرى.")
                return redirect("inquiry:import_excel")

            result = apply_excel_import(file_path, mode)
            request.session.pop("renewal_import_file", None)
            request.session.pop("renewal_import_mode", None)
            request.session.modified = True

            try:
                Path(file_path).unlink(missing_ok=True)
            except Exception:
                pass

            messages.success(
                request,
                f"تم الاستيراد بنجاح. مضاف: {result['created']}، محدث: {result['updated']}، متجاوز: {result['skipped']}، مكرر: {result['duplicates']}."
            )
            return redirect("inquiry:manage_records")

        elif action == "cancel":
            request.session.pop("renewal_import_file", None)
            request.session.pop("renewal_import_mode", None)
            request.session.modified = True
            messages.info(request, "تم إلغاء عملية الاستيراد.")
            return redirect("inquiry:manage_records")

    return render(
        request,
        "inquiry/import_excel.html",
        {
            "form": form,
            "preview": preview,
            "stats": build_admin_stats(),
            "mode": mode,
            "current_total": RenewalRecord.objects.count(),
        },
    )


def build_quick_reply(record):
    if record.status_key == "renewed":
        return (
            "نفيدكم بأن حالة التكليف تظهر في منصة الاستعلام: تم التجديد. "
            "علمًا بأن القرار الرسمي هو المرجع النظامي، وسيتم تزويدكم به عبر القنوات الرسمية من جهة الاختصاص."
        )

    if record.status_key == "not_renewed":
        return (
            "نفيدكم بأن حالة التكليف حسب البيانات المعتمدة هي: لم يتم التجديد. "
            "ويمكن متابعة ما يصدر حيال ذلك عبر القنوات الرسمية، ويُعد القرار الرسمي هو المرجع النظامي."
        )

    if record.status_key == "limited":
        return (
            "نفيدكم بأن حالة التكليف تظهر في منصة الاستعلام: تم التجديد لمدة محددة. "
            "ويُعد القرار الرسمي هو المرجع النظامي للتفاصيل."
        )

    if record.status_key == "pending":
        return (
            "نفيدكم بأن حالة التكليف لا تزال تحت الإجراء وفق البيانات المعتمدة، "
            "وسيتم تحديث الحالة عند اكتمال المعالجة من جهة الاختصاص."
        )

    return (
        f"نفيدكم بأن حالة التكليف تظهر في منصة الاستعلام: {record.status_label}. "
        "ويُعد القرار الرسمي هو المرجع النظامي."
    )




@staff_member_required(login_url="/admin/login/")
def inquiry_settings(request):
    settings_obj = get_inquiry_settings()

    if request.method == "POST":
        form = InquirySettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "تم تحديث إعدادات إتاحة الاستعلام بنجاح.")
            return redirect("inquiry:inquiry_settings")
    else:
        form = InquirySettingsForm(instance=settings_obj)

    return render(
        request,
        "inquiry/inquiry_settings.html",
        {
            "form": form,
            "settings_obj": settings_obj,
            "is_available": settings_obj.is_available(),
            "availability_reason": settings_obj.availability_reason(),
        },
    )


@staff_member_required(login_url="/admin/login/")
def quick_inquiry(request):
    query = ""
    records = []
    searched = False
    error = ""
    no_result_reply = ""

    if request.method == "POST":
        searched = True
        query = (request.POST.get("query") or request.POST.get("national_id") or "").strip()
        national_id = normalize_national_id(query)

        if not query:
            error = "فضلاً أدخل السجل المدني أو الاسم أو الرقم الوزاري أو اسم المدرسة."
        else:
            if national_id:
                records_qs = RenewalRecord.objects.filter(national_id=national_id)
            else:
                records_qs = RenewalRecord.objects.filter(
                    Q(full_name__icontains=query)
                    | Q(ministry_number__icontains=query)
                    | Q(school_name__icontains=query)
                    | Q(sector__icontains=query)
                )

            records = list(records_qs.order_by("full_name", "school_name")[:20])

            for record in records:
                record.quick_reply = build_quick_reply(record)

            if not records:
                error = "لا توجد بيانات مرتبطة بالبيانات المدخلة ضمن حالات التكليف أو النقل أو التجديد لهذه المرحلة."
                no_result_reply = (
                    "نفيدكم بأنه لا توجد بيانات مرتبطة بالبيانات المدخلة ضمن حالات التكليف أو النقل أو التجديد لهذه المرحلة، "
                    "ونأمل التأكد من صحة السجل المدني أو الاسم أو الرقم الوزاري أو مراجعة جهة الاختصاص."
                )

    return render(
        request,
        "inquiry/quick_inquiry.html",
        {
            "searched": searched,
            "query": query,
            "records": records,
            "error": error,
            "no_result_reply": no_result_reply,
        },
    )


@staff_member_required(login_url="/admin/login/")
def inquiry_logs(request):
    query = (request.GET.get("q") or "").strip()
    found = (request.GET.get("found") or "").strip()

    logs = InquiryLog.objects.all().order_by("-created_at")

    if query:
        logs = logs.filter(
            Q(reference_number__icontains=query)
            | Q(national_id__icontains=query)
            | Q(result_name__icontains=query)
            | Q(result_category__icontains=query)
            | Q(result_school__icontains=query)
            | Q(result_status_label__icontains=query)
            | Q(ip_address__icontains=query)
            | Q(user_agent__icontains=query)
        )

    if found == "yes":
        logs = logs.filter(found=True)
    elif found == "no":
        logs = logs.filter(found=False)

    paginator = Paginator(logs, 30)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "query": query,
        "found": found,
        "total_logs": InquiryLog.objects.count(),
        "found_logs": InquiryLog.objects.filter(found=True).count(),
        "not_found_logs": InquiryLog.objects.filter(found=False).count(),
    }
    return render(request, "inquiry/inquiry_logs.html", context)
