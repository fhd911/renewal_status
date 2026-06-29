from django import forms

from .models import InquirySettings, RenewalRecord
from .utils import classify_status, normalize_category, normalize_ministry_number, normalize_national_id


IMPORT_MODE_CHOICES = [
    ("replace", "استبدال البيانات الحالية بالكامل"),
    ("update", "تحديث وإضافة دون حذف البيانات الحالية"),
]


class RenewalRecordForm(forms.ModelForm):
    class Meta:
        model = RenewalRecord
        fields = [
            "national_id",
            "full_name",
            "ministry_number",
            "school_name",
            "sector",
            "gender",
            "current_work",
            "raw_status",
            "non_renewal_reason",
            "admin_note",
            "is_published",
        ]
        labels = {
            "national_id": "السجل المدني",
            "full_name": "الاسم الرباعي",
            "ministry_number": "الرقم الوزاري",
            "school_name": "اسم المدرسة",
            "sector": "القطاع التعليمي",
            "gender": "الجنس / الإدارة",
            "current_work": "العمل الحالي",
            "raw_status": "التجديد",
            "non_renewal_reason": "المبرر في حال عدم التجديد",
            "admin_note": "ملاحظة إدارية",
            "is_published": "إظهار النتيجة للمستفيد",
        }
        widgets = {
            "national_id": forms.TextInput(attrs={"placeholder": "السجل المدني", "inputmode": "numeric"}),
            "full_name": forms.TextInput(attrs={"placeholder": "الاسم الرباعي"}),
            "ministry_number": forms.TextInput(attrs={"placeholder": "الرقم الوزاري"}),
            "school_name": forms.TextInput(attrs={"placeholder": "اسم المدرسة"}),
            "sector": forms.TextInput(attrs={"placeholder": "القطاع التعليمي"}),
            "gender": forms.TextInput(attrs={"placeholder": "بنين / بنات"}),
            "current_work": forms.TextInput(attrs={"placeholder": "مدير / وكيل / موجه طلابي / رائد نشاط"}),
            "raw_status": forms.TextInput(attrs={"placeholder": "يجدد / لا يجدد / يجدد إلى / تحت الإجراء"}),
            "non_renewal_reason": forms.TextInput(attrs={"placeholder": "معلومة داخلية للإدارة فقط"}),
            "admin_note": forms.Textarea(attrs={"rows": 3, "placeholder": "ملاحظة داخلية لا تظهر للمستفيد"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk and not self.initial.get("current_work"):
            self.initial["current_work"] = self.instance.current_work or self.instance.category

    def clean_national_id(self):
        national_id = normalize_national_id(self.cleaned_data.get("national_id"))
        if not national_id:
            raise forms.ValidationError("السجل المدني مطلوب.")
        if len(national_id) < 8:
            raise forms.ValidationError("السجل المدني غير مكتمل.")
        return national_id

    def clean_ministry_number(self):
        return normalize_ministry_number(self.cleaned_data.get("ministry_number"))

    def save(self, commit=True):
        instance = super().save(commit=False)

        instance.category = normalize_category(instance.current_work)
        if not instance.current_work:
            instance.current_work = instance.category

        status = classify_status(instance.raw_status)
        instance.status_key = status["key"]
        instance.status_label = status["label"]
        instance.status_message = status["message"]

        if commit:
            instance.save()
            self.save_m2m()

        return instance


class ExcelImportForm(forms.Form):
    file = forms.FileField(
        label="ملف Excel",
        help_text="الصيغ المدعومة: xlsx",
    )
    mode = forms.ChoiceField(
        label="طريقة الاستيراد",
        choices=IMPORT_MODE_CHOICES,
        initial="replace",
        widget=forms.RadioSelect,
    )

    def clean_file(self):
        uploaded = self.cleaned_data["file"]
        if not uploaded.name.lower().endswith(".xlsx"):
            raise forms.ValidationError("فضلاً ارفع ملف Excel بصيغة xlsx.")
        return uploaded


class InquirySettingsForm(forms.ModelForm):
    class Meta:
        model = InquirySettings
        fields = [
            "is_enabled",
            "start_at",
            "end_at",
            "closed_message",
        ]
        labels = {
            "is_enabled": "إتاحة الاستعلام للمستفيدين",
            "start_at": "بداية الإتاحة",
            "end_at": "نهاية الإتاحة",
            "closed_message": "رسالة تظهر عند إغلاق الاستعلام",
        }
        widgets = {
            "start_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "end_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "closed_message": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "مثال: الاستعلام غير متاح حاليًا، وسيتم فتحه في الموعد المحدد من جهة الاختصاص.",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["start_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["end_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["start_at"].required = False
        self.fields["end_at"].required = False
        self.fields["closed_message"].required = False

    def clean(self):
        cleaned = super().clean()
        start_at = cleaned.get("start_at")
        end_at = cleaned.get("end_at")

        if start_at and end_at and end_at <= start_at:
            raise forms.ValidationError("تاريخ نهاية الإتاحة يجب أن يكون بعد تاريخ البداية.")

        return cleaned
