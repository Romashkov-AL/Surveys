import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Attempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('finished_at', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=500)),
                ('position', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ['position', 'id'],
            },
        ),
        migrations.CreateModel(
            name='Survey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(db_index=True, max_length=150, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
        ),
        migrations.CreateModel(
            name='Choice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=500)),
                ('position', models.PositiveIntegerField(default=0)),
                ('allows_free_text', models.BooleanField(default=False, help_text='При выборе данного варианта, пользователь может ввести свой ответ.')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='choices', to='surveys.question')),
            ],
            options={
                'ordering': ['position', 'id'],
            },
        ),
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('free_text', models.CharField(blank=True, default='', max_length=1000)),
                ('answered_at', models.DateTimeField(auto_now_add=True)),
                ('attempt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='surveys.attempt')),
                ('choice', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='answers', to='surveys.choice')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='surveys.question')),
            ],
        ),
        migrations.AddField(
            model_name='question',
            name='survey',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='surveys.survey'),
        ),
        migrations.AddField(
            model_name='attempt',
            name='survey',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attempts', to='surveys.survey'),
        ),
        migrations.AddField(
            model_name='survey',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='authored_surveys', to='surveys.user'),
        ),
        migrations.AddField(
            model_name='attempt',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attempts', to='surveys.user'),
        ),
        migrations.AddIndex(
            model_name='choice',
            index=models.Index(fields=['question', 'position'], name='surveys_cho_questio_72a9bf_idx'),
        ),
        migrations.AddConstraint(
            model_name='choice',
            constraint=models.UniqueConstraint(fields=('question', 'position'), name='uniq_choice_position_per_question'),
        ),
        migrations.AddIndex(
            model_name='answer',
            index=models.Index(fields=['attempt', 'question'], name='surveys_ans_attempt_0dea68_idx'),
        ),
        migrations.AddIndex(
            model_name='answer',
            index=models.Index(fields=['choice'], name='surveys_ans_choice__3677ce_idx'),
        ),
        migrations.AddConstraint(
            model_name='answer',
            constraint=models.UniqueConstraint(fields=('attempt', 'question'), name='uniq_answer_per_attempt_question'),
        ),
        migrations.AddIndex(
            model_name='question',
            index=models.Index(fields=['survey', 'position'], name='surveys_que_survey__22edeb_idx'),
        ),
        migrations.AddConstraint(
            model_name='question',
            constraint=models.UniqueConstraint(fields=('survey', 'position'), name='uniq_question_position_per_survey'),
        ),
        migrations.AddIndex(
            model_name='survey',
            index=models.Index(fields=['author', '-created_at'], name='surveys_sur_author__124567_idx'),
        ),
        migrations.AddIndex(
            model_name='attempt',
            index=models.Index(fields=['user', 'survey', '-started_at'], name='surveys_att_user_id_acfb17_idx'),
        ),
        migrations.AddIndex(
            model_name='attempt',
            index=models.Index(fields=['survey', 'finished_at'], name='surveys_att_survey__18c82c_idx'),
        ),
        migrations.AddConstraint(
            model_name='attempt',
            constraint=models.UniqueConstraint(condition=models.Q(('finished_at__isnull', True)), fields=('user', 'survey'), name='uniq_open_attempt_per_user_survey'),
        ),
    ]
