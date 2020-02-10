# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracking', '0003_auto_20190722_1418'),
    ]

    operations = [
        migrations.CreateModel(
            name='BodyQueryDictItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.TextField()),
                ('value', models.TextField()),
                ('page_view', models.ForeignKey(to='tracking.Pageview')),
            ],
        ),
    ]
