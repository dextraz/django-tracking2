# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracking', '0003_auto_20190722_1418'),
    ]

    operations = [
        migrations.AddField(
            model_name='pageview',
            name='req_body',
            field=models.TextField(null=True),
        ),
    ]
