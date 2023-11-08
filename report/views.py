import random

from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView, TemplateView, FormView, CreateView, FormView, DeleteView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import transaction
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect

from accounts.decorators import student_required, instructor_required
from .models import *
from .forms import *


@method_decorator([login_required, instructor_required], name='dispatch')
class ReportCreateView(CreateView):
    model = Report
    form_class = ReportAddForm

    def get_context_data(self, *args, **kwargs):
        context = super(ReportCreateView, self).get_context_data(**kwargs)
        context['course'] = Course.objects.get(slug=self.kwargs['slug'])
        if self.request.POST:
            context['form'] = ReportAddForm(self.request.POST)
            # context['report'] = self.request.POST.get('report')
        else:
            context['form'] = ReportAddForm(initial={'course': Course.objects.get(slug=self.kwargs['slug'])})
        return context

    def form_valid(self, form, **kwargs):
        context = self.get_context_data()
        form = context['form']
        with transaction.atomic():
            self.object = form.save()
            if form.is_valid():
                form.instance = self.object
                form.save()
                return redirect('mc_create', slug=self.kwargs['slug'], report_id=form.instance.id)
        return super(ReportCreateView, self).form_invalid(form)


@method_decorator([login_required, instructor_required], name='dispatch')
class ReportUpdateView(UpdateView):
    model = Report
    form_class = ReportAddForm

    def get_context_data(self, *args, **kwargs):
        context = super(ReportUpdateView, self).get_context_data(**kwargs)
        context['course'] = Course.objects.get(slug=self.kwargs['slug'])
        report = Report.objects.get(pk=self.kwargs['pk'])
        if self.request.POST:
            context['form'] = ReportAddForm(self.request.POST, instance=report)
        else:
            context['form'] = ReportAddForm(instance=report)
        return context

    def form_valid(self, form, **kwargs):
        context = self.get_context_data()
        course = context['course']
        form = context['form']
        with transaction.atomic():
            self.object = form.save()
            if form.is_valid():
                form.instance = self.object
                form.save()
                return redirect('report_index', course.slug)
        return super(ReportUpdateView, self).form_invalid(form)


@login_required
@instructor_required
def report_delete(request, slug, pk):
    report = Report.objects.get(pk=pk)
    course = Course.objects.get(slug=slug)
    report.delete()
    messages.success(request, f'successfuly deleted.')
    return redirect('report_index', report.course.slug)


@method_decorator([login_required, instructor_required], name='dispatch')
class MCQuestionCreate(CreateView):
    model = MCQuestion
    form_class = MCQuestionForm

    def get_context_data(self, **kwargs):
        context = super(MCQuestionCreate, self).get_context_data(**kwargs)
        context['course'] = Course.objects.get(slug=self.kwargs['slug'])
        context['report_obj'] = Report.objects.get(id=self.kwargs['report_id'])
        context['reportQuestions'] = Question.objects.filter(report=self.kwargs['report_id']).count()
        if self.request.POST:
            context['form'] = MCQuestionForm(self.request.POST)
            context['formset'] = MCQuestionFormSet(self.request.POST)
        else:
            context['form'] = MCQuestionForm(initial={'report': self.kwargs['report_id']})
            context['formset'] = MCQuestionFormSet()

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        course = context['course']
        with transaction.atomic():
            form.instance.question = self.request.POST.get('content')
            self.object = form.save()
            if formset.is_valid():
                formset.instance = self.object
                formset.save()
                if "another" in self.request.POST:
                    return redirect('mc_create', slug=self.kwargs['slug'], report_id=self.kwargs['report_id'])
                return redirect('report_index', course.slug)
        return super(MCQuestionCreate, self).form_invalid(form)


@login_required
def report_list(request, slug):
    reports = Report.objects.filter(course__slug = slug).order_by('-timestamp')
    course = Course.objects.get(slug = slug)
    return render(request, 'report/report_list.html', {'reports': reports, 'course': course})
    # return render(request, 'report/report_list.html', {'reports': reports})


@method_decorator([login_required, instructor_required], name='dispatch')
class ReportMarkerMixin(object):
    @method_decorator(login_required)
    # @method_decorator(permission_required('report.view_sittings'))
    def dispatch(self, *args, **kwargs):
        return super(ReportMarkerMixin, self).dispatch(*args, **kwargs)


# @method_decorator([login_required, instructor_required], name='get_queryset')
class SittingFilterTitleMixin(object):
    def get_queryset(self):
        queryset = super(SittingFilterTitleMixin, self).get_queryset()
        report_filter = self.request.GET.get('report_filter')
        if report_filter:
            queryset = queryset.filter(report__title__icontains=report_filter)

        return queryset


@method_decorator([login_required], name='dispatch')
class ReportUserProgressView(TemplateView):
    template_name = 'progress.html'

    def dispatch(self, request, *args, **kwargs):
        return super(ReportUserProgressView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ReportUserProgressView, self).get_context_data(**kwargs)
        progress, c = Progress.objects.get_or_create(user=self.request.user)
        context['cat_scores'] = progress.list_all_cat_scores
        context['exams'] = progress.show_exams()
        context['exams_counter'] = progress.show_exams().count()
        return context

from result.models import TakenCourse

@method_decorator([login_required, instructor_required], name='dispatch')
class ReportMarkingList(ReportMarkerMixin, SittingFilterTitleMixin, ListView):
    model = Sitting
    # def get_context_data(self, **kwargs):
    #     context = super(ReportMarkingList, self).get_context_data(**kwargs)
    #     context['queryset_counter'] = super(ReportMarkingList, self).get_queryset().filter(complete=True).filter(course__allocated_course__instructor__pk=self.request.user.id).count()
    #     context['marking_list'] = super(ReportMarkingList, self).get_queryset().filter(complete=True).filter(course__allocated_course__instructor__pk=self.request.user.id)
    #     return context
    def get_queryset(self):
        if self.request.user.is_superuser:
            queryset = super(ReportMarkingList, self).get_queryset().filter(complete=True)
        else:
            queryset = super(ReportMarkingList, self).get_queryset().filter(report__course__allocated_course__instructor__pk=self.request.user.id).filter(complete=True)

        # search by user
        user_filter = self.request.GET.get('user_filter')
        if user_filter:
            queryset = queryset.filter(user__username__icontains=user_filter)
            
        return queryset


@method_decorator([login_required, instructor_required], name='dispatch')
class ReportMarkingDetail(ReportMarkerMixin, DetailView):
    model = Sitting

    def post(self, request, *args, **kwargs):
        sitting = self.get_object()

        q_to_toggle = request.POST.get('qid', None)
        if q_to_toggle:
            q = Question.objects.get_subclass(id=int(q_to_toggle))
            if int(q_to_toggle) in sitting.get_incorrect_questions:
                sitting.remove_incorrect_question(q)
            else:
                sitting.add_incorrect_question(q)

        return self.get(request)

    def get_context_data(self, **kwargs):
        context = super(ReportMarkingDetail, self).get_context_data(**kwargs)
        context['questions'] = context['sitting'].get_questions(with_answers=True)
        return context


# @method_decorator([login_required, student_required], name='dispatch')
@method_decorator([login_required], name='dispatch')
class ReportTake(FormView):
    form_class = QuestionForm
    template_name = 'question.html'
    result_template_name = 'result.html'
    # single_complete_template_name = 'single_complete.html'

    def dispatch(self, request, *args, **kwargs):
        self.report = get_object_or_404(Report, slug=self.kwargs['slug'])
        self.course = get_object_or_404(Course, pk=self.kwargs['pk'])
        reportQuestions = Question.objects.filter(report=self.report).count()
        course = get_object_or_404(Course, pk=self.kwargs['pk'])

        if reportQuestions <= 0:
            messages.warning(request, f'Question set of the report is empty. try later!')
            return redirect('report_index', self.course.slug)

        if self.report.draft and not request.user.has_perm('report.change_report'):
            raise PermissionDenied

        self.sitting = Sitting.objects.user_sitting(request.user, self.report, self.course)

        if self.sitting is False:
            # return render(request, self.single_complete_template_name)
            messages.info(request, f'You have already sat this exam and only one sitting is permitted')
            return redirect('report_index', self.course.slug)

        return super(ReportTake, self).dispatch(request, *args, **kwargs)

    def get_form(self, *args, **kwargs):
        self.question = self.sitting.get_first_question()
        self.progress = self.sitting.progress()

        if self.question.__class__ is Essay_Question:
            form_class = EssayForm
        else:
            form_class = self.form_class

        return form_class(**self.get_form_kwargs())

    def get_form_kwargs(self):
        kwargs = super(ReportTake, self).get_form_kwargs()

        return dict(kwargs, question=self.question)

    def form_valid(self, form):
        self.form_valid_user(form)
        if self.sitting.get_first_question() is False:
            return self.final_result_user()

        self.request.POST = {}

        return super(ReportTake, self).get(self, self.request)

    def get_context_data(self, **kwargs):
        context = super(ReportTake, self).get_context_data(**kwargs)
        context['question'] = self.question
        context['report'] = self.report
        context['course'] = get_object_or_404(Course, pk=self.kwargs['pk'])
        if hasattr(self, 'previous'):
            context['previous'] = self.previous
        if hasattr(self, 'progress'):
            context['progress'] = self.progress
        return context

    def form_valid_user(self, form):
        progress, c = Progress.objects.get_or_create(user=self.request.user)
        guess = form.cleaned_data['answers']
        is_correct = self.question.check_if_correct(guess)

        if is_correct is True:
            self.sitting.add_to_score(1)
            progress.update_score(self.question, 1, 1)
        else:
            self.sitting.add_incorrect_question(self.question)
            progress.update_score(self.question, 0, 1)

        if self.report.answers_at_end is not True:
            self.previous = {
                'previous_answer': guess,
                'previous_outcome': is_correct,
                'previous_question': self.question,
                'answers': self.question.get_choices(),
                'question_type': {self.question.__class__.__name__: True}
            }
        else:
            self.previous = {}

        self.sitting.add_user_answer(self.question, guess)
        self.sitting.remove_first_question()

    def final_result_user(self):
        results = {
            'course': get_object_or_404(Course, pk=self.kwargs['pk']),
            'report': self.report,
            'score': self.sitting.get_current_score,
            'max_score': self.sitting.get_max_score,
            'percent': self.sitting.get_percent_correct,
            'sitting': self.sitting,
            'previous': self.previous,
            'course': get_object_or_404(Course, pk=self.kwargs['pk'])
        }

        self.sitting.mark_report_complete()

        if self.report.answers_at_end:
            results['questions'] = self.sitting.get_questions(with_answers=True)
            results['incorrect_questions'] = self.sitting.get_incorrect_questions

        if self.report.exam_paper is False or self.request.user.is_superuser or self.request.user.is_instructor :
            self.sitting.delete()

        return render(self.request, self.result_template_name, results)
