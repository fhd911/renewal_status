from django.db import models
from django.utils import timezone


class RenewalRecord(models.Model):
    national_id = models.CharField("السجل المدني", max_length=20, db_index=True)
    mobile_last4 = models.CharField("آخر 4 أرقام من الجوال", max_length=4, blank=True, default="")

    full_name = models.CharField("الاسم الرباعي", max_length=255)
    ministry_number = models.CharField("الرقم الوزاري", max_length=100, blank=True, default="")
    school_name = models.CharField("اسم المدرسة", max_length=255, blank=True, default="")
    sector = models.CharField("القطاع التعليمي", max_length=255, blank=True, default="")
    gender = models.CharField("الجنس / الإدارة", max_length=50, blank=True, default="")

    current_work = models.CharField("العمل الحالي", max_length=100, blank=True, default="")
    category = models.CharField("الفئة", max_length=100, blank=True, default="")

    raw_status = models.CharField("التجديد", max_length=255, blank=True, default="")
    status_key = models.CharField("رمز الحالة", max_length=50, blank=True, default="pending")
    status_label = models.CharField("الحالة المعروضة", max_length=100, blank=True, default="تحت الإجراء")
    status_message = models.TextField("رسالة الحالة", blank=True, default="")

    non_renewal_reason = models.CharField("المبرر في حال عدم التجديد", max_length=255, blank=True, default="")
    admin_note = models.TextField("ملاحظة إدارية", blank=True, default="")

    is_published = models.BooleanField("منشور", default=True)
    created_at = models.DateTimeField("تاريخ الإضافة", auto_now_add=True)
    updated_at = models.DateTimeField("تاريخ التحديث", auto_now=True)

    class Meta:
        verbose_name = "سجل استعلام"
        verbose_name_plural = "سجلات الاستعلام"
        ordering = ["full_name", "school_name"]
        indexes = [
            models.Index(fields=["national_id"]),
            models.Index(fields=["ministry_number"]),
            models.Index(fields=["category"]),
            models.Index(fields=["status_key"]),
        ]

    def __str__(self):
        return f"{self.full_name} - {self.national_id}"


class InquiryLog(models.Model):
    reference_number = models.CharField("رقم الاستعلام", max_length=30, blank=True, default="", db_index=True)
    national_id = models.CharField("السجل المدني المدخل", max_length=20, db_index=True)
    mobile_last4 = models.CharField("آخر 4 أرقام مدخلة", max_length=4, blank=True, default="")
    found = models.BooleanField("ظهرت نتيجة", default=False)

    result_name = models.CharField("الاسم وقت الاستعلام", max_length=255, blank=True, default="")
    result_category = models.CharField("الفئة وقت الاستعلام", max_length=100, blank=True, default="")
    result_school = models.CharField("المدرسة وقت الاستعلام", max_length=255, blank=True, default="")
    result_sector = models.CharField("القطاع وقت الاستعلام", max_length=255, blank=True, default="")
    result_status_label = models.CharField("الحالة وقت الاستعلام", max_length=100, blank=True, default="")
    result_raw_status = models.CharField("الحالة في البيانات وقت الاستعلام", max_length=255, blank=True, default="")

    ip_address = models.CharField("IP", max_length=100, blank=True, default="")
    user_agent = models.TextField("المتصفح", blank=True, default="")
    created_at = models.DateTimeField("وقت الاستعلام", auto_now_add=True)

    class Meta:
        verbose_name = "سجل عملية استعلام"
        verbose_name_plural = "سجل عمليات الاستعلام"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["reference_number"]),
            models.Index(fields=["national_id"]),
            models.Index(fields=["found"]),
        ]

    def __str__(self):
        return self.reference_number or self.national_id

class InquirySettings(models.Model):
    is_enabled = models.BooleanField("إتاحة الاستعلام للمستفيدين", default=True)
    start_at = models.DateTimeField("بداية الإتاحة", null=True, blank=True)
    end_at = models.DateTimeField("نهاية الإتاحة", null=True, blank=True)
    closed_message = models.TextField(
        "رسالة الإغلاق",
        blank=True,
        default="الاستعلام غير متاح حاليًا، وسيتم فتحه في الموعد المحدد من جهة الاختصاص.",
    )
    updated_at = models.DateTimeField("آخر تحديث", auto_now=True)

    class Meta:
        verbose_name = "إعداد الاستعلام"
        verbose_name_plural = "إعدادات الاستعلام"

    def __str__(self):
        return "إعدادات إتاحة الاستعلام"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def is_available(self, now=None):
        now = now or timezone.now()

        if not self.is_enabled:
            return False

        if self.start_at and now < self.start_at:
            return False

        if self.end_at and now > self.end_at:
            return False

        return True

    def availability_reason(self, now=None):
        now = now or timezone.now()

        if not self.is_enabled:
            return "مغلق يدويًا"

        if self.start_at and now < self.start_at:
            return "لم تبدأ فترة الإتاحة"

        if self.end_at and now > self.end_at:
            return "انتهت فترة الإتاحة"

        return "متاح"

    def public_closed_message(self):
        return self.closed_message or "الاستعلام غير متاح حاليًا، وسيتم فتحه في الموعد المحدد من جهة الاختصاص."
