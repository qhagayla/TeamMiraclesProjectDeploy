from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Avg, Max, Min, Count
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView
from django.core.paginator import Paginator
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from accounts.models import User, Student
from app.models import Session, Semester
from result.models import TakenCourse
from accounts.decorators import instructor_required, student_required
from .forms import (
    StratumForm, CourseAddForm, CourseAllocationForm, 
    EditCourseAllocationForm, UploadFormFile, UploadFormVideo
)
from .models import Stratum, Course, CourseAllocation, Upload, UploadVideo


# ########################################################
# Stratum views
# ########################################################
@login_required
def stratum_view(request):
    stratums = Stratum.objects.all()

    stratum_filter = request.GET.get('stratum_filter')
    if stratum_filter:
        stratums = Stratum.objects.filter(title__icontains=stratum_filter)

    return render(request, 'course/stratum_list.html', {
        'title': "Stratums | DjangoSMS",
        'stratums': stratums,
    })


@login_required
@instructor_required
def stratum_add(request):
    if request.method == 'POST':
        form = StratumForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, request.POST.get('title') + ' stratum has been created.')
            return redirect('stratums')
        else:
            messages.error(request, 'Correct the error(S) below.')
    else:
        form = StratumForm()

    return render(request, 'course/stratum_add.html', {
        'title': "Add Stratum | DjangoSMS",
        'form': form,
    })


@login_required
def stratum_detail(request, pk):
    stratum = Stratum.objects.get(pk=pk)
    courses = Course.objects.filter(stratum_id=pk).order_by('-year')
    credits = Course.objects.aggregate(Sum('credit'))

    paginator = Paginator(courses, 10)
    page = request.GET.get('page')

    courses = paginator.get_page(page)

    return render(request, 'course/stratum_single.html', {
        'title': stratum.title,
        'stratum': stratum, 'courses': courses, 'credits': credits
    }, )


@login_required
@instructor_required
def stratum_edit(request, pk):
    stratum = Stratum.objects.get(pk=pk)

    if request.method == 'POST':
        form = StratumForm(request.POST, instance=stratum)
        if form.is_valid():
            form.save()
            messages.success(request, str(request.POST.get('title')) + ' stratum has been updated.')
            return redirect('stratums')
    else:
        form = StratumForm(instance=stratum)

    return render(request, 'course/stratum_add.html', {
        'title': "Edit Stratum | DjangoSMS",
        'form': form
    })


@login_required
@instructor_required
def stratum_delete(request, pk):
    stratum = Stratum.objects.get(pk=pk)
    title = stratum.title
    stratum.delete()
    messages.success(request, 'Stratum ' + title + ' has been deleted.')

    return redirect('stratums')
# ########################################################

# ########################################################
# Course views
# ########################################################
@login_required
def course_single(request, slug):
    course = Course.objects.get(slug=slug)
    files = Upload.objects.filter(course__slug=slug)
    videos = UploadVideo.objects.filter(course__slug=slug)

    # instructors = User.objects.filter(allocated_instructor__pk=course.id)
    instructors = CourseAllocation.objects.filter(courses__pk=course.id)

    return render(request, 'course/course_single.html', {
        'title': course.title,
        'course': course,
        'files': files,
        'videos': videos,
        'instructors': instructors,
        'media_url': settings.MEDIA_ROOT,
    }, )


@login_required
@instructor_required
def course_add(request, pk):
    users = User.objects.all()
    if request.method == 'POST':
        form = CourseAddForm(request.POST)
        course_name = request.POST.get('title')
        course_code = request.POST.get('code')
        if form.is_valid():
            form.save()
            messages.success(request, (course_name + '(' + course_code + ')' + ' has been created.'))
            return redirect('stratum_detail', pk=request.POST.get('stratum'))
        else:
            messages.error(request, 'Correct the error(s) below.')
    else:
        form = CourseAddForm(initial={'stratum': Stratum.objects.get(pk=pk)})

    return render(request, 'course/course_add.html', {
        'title': "Add Course | DjangoSMS",
        'form': form, 'stratum': pk, 'users': users
    }, )


@login_required
@instructor_required
def course_edit(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if request.method == 'POST':
        form = CourseAddForm(request.POST, instance=course)
        course_name = request.POST.get('title')
        course_code = request.POST.get('code')
        if form.is_valid():
            form.save()
            messages.success(request, (course_name + '(' + course_code + ')' + ' has been updated.'))
            return redirect('stratum_detail', pk=request.POST.get('stratum'))
        else:
            messages.error(request, 'Correct the error(s) below.')
    else:
        form = CourseAddForm(instance=course)

    return render(request, 'course/course_add.html', {
        'title': "Edit Course | DjangoSMS",
        # 'form': form, 'stratum': pk, 'course': pk
        'form': form
    }, )


@login_required
@instructor_required
def course_delete(request, slug):
    course = Course.objects.get(slug=slug)
    # course_name = course.title
    course.delete()
    messages.success(request, 'Course ' + course.title + ' has been deleted.')

    return redirect('stratum_detail', pk=course.stratum.id)
# ########################################################


# ########################################################
# Course Allocation
# ########################################################
@method_decorator([login_required], name='dispatch')
class CourseAllocationFormView(CreateView):
    form_class = CourseAllocationForm
    template_name = 'course/course_allocation_form.html'

    def get_form_kwargs(self):
        kwargs = super(CourseAllocationFormView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # if a staff has been allocated a course before update it else create new
        instructor = form.cleaned_data['instructor']
        selected_courses = form.cleaned_data['courses']
        courses = ()
        for course in selected_courses:
            courses += (course.pk,)
        # print(courses)

        try:
            a = CourseAllocation.objects.get(instructor=instructor)
        except:
            a = CourseAllocation.objects.create(instructor=instructor)
        for i in range(0, selected_courses.count()):
            a.courses.add(courses[i])
            a.save()
        return redirect('course_allocation_view')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Assign Course | DjangoSMS"
        return context


@login_required
def course_allocation_view(request):
    allocated_courses = CourseAllocation.objects.all()
    return render(request, 'course/course_allocation_view.html', {
        'title': "Course Allocations | DjangoSMS",
        "allocated_courses": allocated_courses
    })


@login_required
@instructor_required
def edit_allocated_course(request, pk):
    allocated = get_object_or_404(CourseAllocation, pk=pk)
    if request.method == 'POST':
        form = EditCourseAllocationForm(request.POST, instance=allocated)
        if form.is_valid():
            form.save()
            messages.success(request, 'course assigned has been updated.')
            return redirect('course_allocation_view')
    else:
        form = EditCourseAllocationForm(instance=allocated)

    return render(request, 'course/course_allocation_form.html', {
        'title': "Edit Course Allocated | DjangoSMS",
        'form': form, 'allocated': pk
    }, )


@login_required
@instructor_required
def deallocate_course(request, pk):
    course = CourseAllocation.objects.get(pk=pk)
    course.delete()
    messages.success(request, 'successfully deallocate!')
    return redirect("course_allocation_view")
# ########################################################


# ########################################################
# File Upload views
# ########################################################
@login_required
@instructor_required
#@student_required
def handle_file_upload(request, slug):
    course = Course.objects.get(slug=slug)
    if request.method == 'POST':
        form = UploadFormFile(request.POST, request.FILES, {'course': course})
        # file_name = request.POST.get('name')
        if form.is_valid():
            form.save()
            messages.success(request, (request.POST.get('title') + ' has been uploaded.'))
            return redirect('course_detail', slug=slug)
    else:
        form = UploadFormFile()
    return render(request, 'upload/upload_file_form.html', {
        'title': "File Upload | DjangoSMS",
        'form': form, 'course': course
    })


@login_required
@instructor_required
#@student_required
def handle_file_edit(request, slug, file_id):
    course = Course.objects.get(slug=slug)
    instance = Upload.objects.get(pk=file_id)
    if request.method == 'POST':
        form = UploadFormFile(request.POST, request.FILES, instance=instance)
        # file_name = request.POST.get('name')
        if form.is_valid():
            form.save()
            messages.success(request, (request.POST.get('title') + ' has been updated.'))
            return redirect('course_detail', slug=slug)
    else:
        form = UploadFormFile(instance=instance)

    return render(request, 'upload/upload_file_form.html', {
        'title': instance.title,
        'form': form, 'course': course})


def handle_file_delete(request, slug, file_id):
    file = Upload.objects.get(pk=file_id)
    # file_name = file.name
    file.delete()

    messages.success(request, (file.title + ' has been deleted.'))
    return redirect('course_detail', slug=slug)

# ########################################################
# Video Upload views
# ########################################################
@login_required
@instructor_required
def handle_video_upload(request, slug):
    course = Course.objects.get(slug=slug)
    if request.method == 'POST':
        form = UploadFormVideo(request.POST, request.FILES, {'course': course})
        if form.is_valid():
            form.save()
            messages.success(request, (request.POST.get('title') + ' has been uploaded.'))
            return redirect('course_detail', slug=slug)
    else:
        form = UploadFormVideo()
    return render(request, 'upload/upload_video_form.html', {
        'title': "Video Upload | DjangoSMS",
        'form': form, 'course': course
    })


@login_required
# @instructor_required
def handle_video_single(request, slug, video_slug):
    course = get_object_or_404(Course, slug=slug)
    video = get_object_or_404(UploadVideo, slug=video_slug)
    return render(request, 'upload/video_single.html', {'video': video})


@login_required
@instructor_required
def handle_video_edit(request, slug, video_slug):
    course = Course.objects.get(slug=slug)
    instance = UploadVideo.objects.get(slug=video_slug)
    if request.method == 'POST':
        form = UploadFormVideo(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, (request.POST.get('title') + ' has been updated.'))
            return redirect('course_detail', slug=slug)
    else:
        form = UploadFormVideo(instance=instance)

    return render(request, 'upload/upload_video_form.html', {
        'title': instance.title,
        'form': form, 'course': course})


def handle_video_delete(request, slug, video_slug):
    video = get_object_or_404(UploadVideo, slug=video_slug)
    # video = UploadVideo.objects.get(slug=video_slug)
    video.delete()

    messages.success(request, (video.title + ' has been deleted.'))
    return redirect('course_detail', slug=slug)
# ########################################################


# ########################################################
# Course Registration
# ########################################################
@login_required
@student_required
def course_registration(request):
    if request.method == 'POST':
        ids = ()
        data = request.POST.copy()
        data.pop('csrfmiddlewaretoken', None)  # remove csrf_token
        for key in data.keys():
            ids = ids + (str(key),)
        for s in range(0, len(ids)):
            student = Student.objects.get(student__pk=request.user.id)
            course = Course.objects.get(pk=ids[s])
            obj = TakenCourse.objects.create(student=student, course=course)
            obj.save()
            messages.success(request, 'Courses Registered Successfully!')
        return redirect('course_registration')
    else:
        # student = Student.objects.get(student__pk=request.user.id)
        student = get_object_or_404(Student, student__id=request.user.id)
        taken_courses = TakenCourse.objects.filter(student__student__id=request.user.id)
        t = ()
        for i in taken_courses:
            t += (i.course.pk,)
        current_semester = Semester.objects.get(is_current_semester=True)

        courses = Course.objects.filter(stratum__pk=student.section.id, status=student.status, semester=current_semester
        ).exclude(id__in=t).order_by('year')
        all_courses = Course.objects.filter(status=student.status, stratum__pk=student.section.id)

        no_course_is_registered = False  # Check if no course is registered
        all_courses_are_registered = False

        registered_courses = Course.objects.filter(status=student.status).filter(id__in=t)
        if registered_courses.count() == 0:  # Check if number of registered courses is 0
            no_course_is_registered = True

        if registered_courses.count() == all_courses.count():
            all_courses_are_registered = True

        total_first_semester_credit = 0
        total_sec_semester_credit = 0
        total_registered_credit = 0
        for i in courses:
            if i.semester == "First":
                total_first_semester_credit += int(i.credit)
            if i.semester == "Second":
                total_sec_semester_credit += int(i.credit)
        for i in registered_courses:
            total_registered_credit += int(i.credit)
        context = {
            "is_calender_on": True,
            "all_courses_are_registered": all_courses_are_registered,
            "no_course_is_registered": no_course_is_registered,
            "current_semester": current_semester,
            "courses": courses,
            "total_first_semester_credit": total_first_semester_credit,
            "total_sec_semester_credit": total_sec_semester_credit,
            "registered_courses": registered_courses,
            "total_registered_credit": total_registered_credit,
            "student": student,
        }
        return render(request, 'course/course_registration.html', context)


@login_required
@student_required
def course_drop(request):
    if request.method == 'POST':
        ids = ()
        data = request.POST.copy()
        data.pop('csrfmiddlewaretoken', None)  # remove csrf_token
        for key in data.keys():
            ids = ids + (str(key),)
        for s in range(0, len(ids)):
            student = Student.objects.get(student__pk=request.user.id)
            course = Course.objects.get(pk=ids[s])
            obj = TakenCourse.objects.get(student=student, course=course)
            obj.delete()
            messages.success(request, 'Successfully Dropped!')
        return redirect('course_registration')
# ########################################################


@login_required
def user_course_list(request):
    if request.user.is_instructor:
        courses = Course.objects.filter(allocated_course__instructor__pk=request.user.id)

        return render(request, 'course/user_course_list.html', {'courses': courses})

    elif request.user.is_student:
        student = Student.objects.get(student__pk=request.user.id)
        taken_courses = TakenCourse.objects.filter(student__student__id=student.student.id)
        courses = Course.objects.filter(status=student.status).filter(stratum__pk=student.section.id)

        return render(request, 'course/user_course_list.html', {
            'student': student,
            'taken_courses': taken_courses,
            'courses': courses
        })

    else:
        return render(request, 'course/user_course_list.html')

@login_required
#@instructor_required
@student_required
def handle_file_upload(request, slug):
    course = Course.objects.get(slug=slug)
    if request.method == 'POST':
        form = UploadFormFile(request.POST, request.FILES, {'course': course})
        # file_name = request.POST.get('name')
        if form.is_valid():
            form.save()
            messages.success(request, (request.POST.get('title') + ' has been uploaded.'))
            return redirect('course_detail', slug=slug)
    else:
        form = UploadFormFile()
    return render(request, 'upload/upload_file_form.html', {
        'title': "File Upload | DjangoSMS",
        'form': form, 'course': course
    })


@login_required
#@instructor_required
@student_required
def handle_file_edit(request, slug, file_id):
    course = Course.objects.get(slug=slug)
    instance = Upload.objects.get(pk=file_id)
    if request.method == 'POST':
        form = UploadFormFile(request.POST, request.FILES, instance=instance)
        # file_name = request.POST.get('name')
        if form.is_valid():
            form.save()
            messages.success(request, (request.POST.get('title') + ' has been updated.'))
            return redirect('course_detail', slug=slug)
    else:
        form = UploadFormFile(instance=instance)

    return render(request, 'upload/upload_file_form.html', {
        'title': instance.title,
        'form': form, 'course': course})


def handle_file_delete(request, slug, file_id):
    file = Upload.objects.get(pk=file_id)
    # file_name = file.name
    file.delete()

    messages.success(request, (file.title + ' has been deleted.'))
    return redirect('course_detail', slug=slug)


@login_required
@student_required
def handle_video_upload(request, slug):
    course = Course.objects.get(slug=slug)
    if request.method == 'POST':
        form = UploadFormVideo(request.POST, request.FILES, {'course': course})
        if form.is_valid():
            form.save()
            messages.success(request, (request.POST.get('title') + ' has been uploaded.'))
            return redirect('course_detail', slug=slug)
    else:
        form = UploadFormVideo()
    return render(request, 'upload/upload_video_form.html', {
        'title': "Video Upload | DjangoSMS",
        'form': form, 'course': course
    })


@login_required
# @instructor_required
def handle_video_single(request, slug, video_slug):
    course = get_object_or_404(Course, slug=slug)
    video = get_object_or_404(UploadVideo, slug=video_slug)
    return render(request, 'upload/video_single.html', {'video': video})


@login_required
@student_required
def handle_video_edit(request, slug, video_slug):
    course = Course.objects.get(slug=slug)
    instance = UploadVideo.objects.get(slug=video_slug)
    if request.method == 'POST':
        form = UploadFormVideo(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, (request.POST.get('title') + ' has been updated.'))
            return redirect('course_detail', slug=slug)
    else:
        form = UploadFormVideo(instance=instance)

    return render(request, 'upload/upload_video_form.html', {
        'title': instance.title,
        'form': form, 'course': course})


def handle_video_delete(request, slug, video_slug):
    video = get_object_or_404(UploadVideo, slug=video_slug)
    # video = UploadVideo.objects.get(slug=video_slug)
    video.delete()

    messages.success(request, (video.title + ' has been deleted.'))
    return redirect('course_detail', slug=slug)