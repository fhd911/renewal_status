# Generated for Renewal Status V7

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inquiry", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="renewalrecord",
            name="mobile_last4",
            field=models.CharField(blank=True, default="", max_length=4, verbose_name="آخر 4 أرقام من الجوال"),
        ),
        migrations.AddField(
            model_name="inquirylog",
            name="reference_number",
            field=models.CharField(blank=True, db_index=True, default="", max_length=30, verbose_name="رقم الاستعلام"),
        ),
        migrations.AddField(
            model_name="inquirylog",
            name="mobile_last4",
            field=models.CharField(blank=True, default="", max_length=4, verbose_name="آخر 4 أرقام مدخلة"),
        ),
        migrations.AddField(
            model_name="inquirylog",
            name="result_name",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="الاسم وقت الاستعلام"),
        ),
        migrations.AddField(
            model_name="inquirylog",
            name="result_category",
            field=models.CharField(blank=True, default="", max_length=100, verbose_name="الفئة وقت الاستعلام"),
        ),
        migrations.AddField(
            model_name="inquirylog",
            name="result_school",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="المدرسة وقت الاستعلام"),
        ),
        migrations.AddField(
            model_name="inquirylog",
            name="result_sector",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="القطاع وقت الاستعلام"),
        ),
        migrations.AddField(
            model_name="inquirylog",
            name="result_status_label",
            field=models.CharField(blank=True, default="", max_length=100, verbose_name="الحالة وقت الاستعلام"),
        ),
        migrations.AddField(
            model_name="inquirylog",
            name="result_raw_status",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="الحالة في البيانات وقت الاستعلام"),
        ),
        migrations.AddIndex(
            model_name="inquirylog",
            index=models.Index(fields=["reference_number"], name="inquiry_inq_referen_5a0b8e_idx"),
        ),
    ]
