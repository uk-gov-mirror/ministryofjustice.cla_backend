# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [("legalaid", "0025_case_audit_log")]

    operations = [
        migrations.AddField(
            model_name="eligibilitycheck",
            name="in_category_skip_income_check",
            field=models.NullBooleanField(default=None),
            preserve_default=True,
        )
    ]
