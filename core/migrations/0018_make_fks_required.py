# Generated manually to make FK fields required

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def delete_existing_policies(apps, schema_editor):
    """Delete any existing policies since table is new and FKs need to be required"""
    Policy_Main = apps.get_model('core', 'Policy_Main')
    Policy_Main.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0017_policy_main'),
    ]

    operations = [
        # Delete any existing rows first (table is new, so likely empty)
        migrations.RunPython(delete_existing_policies, migrations.RunPython.noop),
        
        # Make all FK fields required
        migrations.AlterField(
            model_name='policy_main',
            name='AgentBranchId',
            field=models.ForeignKey(db_column='AgentBranchId', on_delete=django.db.models.deletion.PROTECT, related_name='policies', to='core.ref_branch'),
        ),
        migrations.AlterField(
            model_name='policy_main',
            name='AgentChannelId',
            field=models.ForeignKey(db_column='AgentChannelId', on_delete=django.db.models.deletion.PROTECT, related_name='policies', to='core.ref_channel'),
        ),
        migrations.AlterField(
            model_name='policy_main',
            name='AgentId',
            field=models.ForeignKey(db_column='AgentId', on_delete=django.db.models.deletion.PROTECT, related_name='agent_policies', to='core.refclient'),
        ),
        migrations.AlterField(
            model_name='policy_main',
            name='ApprovedBy',
            field=models.ForeignKey(db_column='ApprovedBy', on_delete=django.db.models.deletion.PROTECT, related_name='approved_policies', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='policy_main',
            name='CurrencyId',
            field=models.ForeignKey(db_column='CurrencyId', on_delete=django.db.models.deletion.PROTECT, related_name='policies', to='core.ref_currency'),
        ),
        migrations.AlterField(
            model_name='policy_main',
            name='PolicyTemplateId',
            field=models.ForeignKey(db_column='PolicyTemplateId', on_delete=django.db.models.deletion.PROTECT, related_name='policies', to='core.ref_policy_template'),
        ),
    ]
