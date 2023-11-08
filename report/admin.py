from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext_lazy as _

from .models import Report, Progress, Question, MCQuestion, Choice, Essay_Question, Sitting


class ChoiceInline(admin.TabularInline):
    model = Choice


class ReportAdminForm(forms.ModelForm):

    class Meta:
        model = Report
        exclude = []

    questions = forms.ModelMultipleChoiceField(
        queryset=Question.objects.all().select_subclasses(),
        required=False,
        label=_("Questions"),
        widget=FilteredSelectMultiple(
            verbose_name=_("Questions"),
            is_stacked=False))

    def __init__(self, *args, **kwargs):
        super(ReportAdminForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['questions'].initial = self.instance.question_set.all().select_subclasses()

    def save(self, commit=True):
        report = super(ReportAdminForm, self).save(commit=False)
        report.save()
        report.question_set.set(self.cleaned_data['questions'])
        self.save_m2m()
        return report


class ReportAdmin(admin.ModelAdmin):
    form = ReportAdminForm

    list_display = ('title', )
    # list_filter = ('category',)
    search_fields = ('description', 'category', )


class MCQuestionAdmin(admin.ModelAdmin):
    list_display = ('content', )
    # list_filter = ('category',)
    fields = ('content', 'figure', 'report', 'explanation', 'choice_order')

    search_fields = ('content', 'explanation')
    filter_horizontal = ('report',)

    inlines = [ChoiceInline]


class ProgressAdmin(admin.ModelAdmin):
    search_fields = ('user', 'score', )


class EssayQuestionAdmin(admin.ModelAdmin):
    list_display = ('content', )
    # list_filter = ('category',)
    fields = ('content', 'report', 'explanation', )
    search_fields = ('content', 'explanation')
    filter_horizontal = ('report',)

admin.site.register(Report, ReportAdmin)
admin.site.register(MCQuestion, MCQuestionAdmin)
admin.site.register(Progress, ProgressAdmin)
admin.site.register(Essay_Question, EssayQuestionAdmin)
admin.site.register(Sitting)
