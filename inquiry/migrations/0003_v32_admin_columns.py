# Generated for Renewal Status V32 - internal admin columns

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inquiry", "0002_v7_mobile_logs"),
    ]

    operations = [
        migrations.AddField(
            model_name="renewalrecord",
            name="ministry_number",
            field=models.CharField(blank=True, default="", max_length=100, verbose_name="الرقم الوزاري"),
        ),
        migrations.AddField(
            model_name="renewalrecord",
            name="gender",
            field=models.CharField(blank=True, default="", max_length=50, verbose_name="الجنس / الإدارة"),
        ),
        migrations.AddField(
            model_name="renewalrecord",
            name="current_work",
            field=models.CharField(blank=True, default="", max_length=100, verbose_name="العمل الحالي"),
        ),
        migrations.AddField(
            model_name="renewalrecord",
            name="non_renewal_reason",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="المبرر في حال عدم التجديد"),
        ),
        migrations.AddField(
            model_name="renewalrecord",
            name="admin_note",
            field=models.TextField(blank=True, default="", verbose_name="ملاحظة إدارية"),
        ),
        migrations.AddIndex(
            model_name="renewalrecord",
            index=models.Index(fields=["ministry_number"], name="inquiry_ren_ministr_f23c16_idx"),
        ),
    ]
