from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inquiry", "0003_v32_admin_columns"),
    ]

    operations = [
        migrations.CreateModel(
            name="InquirySettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_enabled", models.BooleanField(default=True, verbose_name="إتاحة الاستعلام للمستفيدين")),
                ("start_at", models.DateTimeField(blank=True, null=True, verbose_name="بداية الإتاحة")),
                ("end_at", models.DateTimeField(blank=True, null=True, verbose_name="نهاية الإتاحة")),
                ("closed_message", models.TextField(blank=True, default="الاستعلام غير متاح حاليًا، وسيتم فتحه في الموعد المحدد من جهة الاختصاص.", verbose_name="رسالة الإغلاق")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")),
            ],
            options={
                "verbose_name": "إعداد الاستعلام",
                "verbose_name_plural": "إعدادات الاستعلام",
            },
        ),
    ]
