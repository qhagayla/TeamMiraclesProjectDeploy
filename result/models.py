from django.db import models
from django.urls import reverse

from accounts.models import Student
from app.models import Session, Semester
from course.models import Course

YEARS = (
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (4, '5'),
        (4, '6'),
    )

# STATUS_COURSE = "Status course"
REGULAR_STUDENT = "Regular"
IRREGULAR_STUDENT = "Irregular"

STATUS = (
    # (STATUS_COURSE, "Status course"),
    (REGULAR_STUDENT, "Regular Student"),
    (IRREGULAR_STUDENT, "Irregular Student"),
)

FIRST = "First"
SECOND = "Second"
THIRD = "Third"

SEMESTER = (
    (FIRST, "First"),
    (SECOND, "Second"),
    (THIRD, "Third"),
)

Excellent = "Excellent"
Superior = "Superior"
Meritorious = "Meritorious"
Very_Good = "Very Good"
Good = "Good"
Very_Satisfactory = "Very Satisfactory"
Satisfactory = "Satisfactory"
Fair = "Fair"
Passing = "Passing"
Incomplete = "Incomplete"
Failed = "Failed"
NG = "NG"

GRADE = (
        (Excellent, "Excellent"),
        (Superior, "Superior"),
        (Meritorious, "Meritorious"),
        (Very_Good, "Very Good"),
        (Good, "Good"),
        (Very_Satisfactory, "Very Satisfactory"),
        (Satisfactory, "Satisfactory"),
        (Fair, "Fair"),
        (Passing, "Passing"),
        (Incomplete, "Incomplete"),
        (Failed, "Failed"),
        (NG, "NG"),
)

PASS = "PASS"
FAIL = "FAIL"

COMMENT = (
    (PASS, "PASS"),
    (FAIL, "FAIL"),
)


class TakenCourseManager(models.Manager):
    def new_or_get(self, request):
        cart_id = request.session.get("cart_id", None)
        qs = self.get_queryset().filter(id=cart_id)
        if qs.count() == 1:
            new_obj = False
            cart_obj = qs.first()
            if request.user.is_authenticated() and cart_obj.user is None:
                cart_obj.user = request.user
                cart_obj.save()
        else:
            cart_obj = Cart.objects.new(user=request.user)
            new_obj = True
            request.session['cart_id'] = cart_obj.id
        return cart_obj, new_obj

    def new(self, user=None):
        user_obj = None
        if user is not None:
            if user.is_authenticated():
                user_obj = user
        return self.model.objects.create(user=user_obj)


class TakenCourse(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='taken_courses')
    report = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    attendance = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    total = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    grade = models.CharField(choices=GRADE, max_length=200, blank=True)
    point = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    comment = models.CharField(choices=COMMENT, max_length=200, blank=True)

    def get_absolute_url(self):
        return reverse('course_detail', kwargs={'slug': self.course.slug})

    def __str__(self):
        return "{0} ({1})".format(self.course.title, self.course.code)

    # @staticmethod
    def get_total(self, report, attendance):
        return (float(report) + float(attendance)) / 2

    # @staticmethod
    def get_grade(self, total):
        # total = float(assignment) + float(mid_exam) + float(report) + float(attendance) + float(final_exam)
        # total = self.get_total(assignment=assignment, mid_exam=mid_exam, report=report, attendance=attendance, final_exam=final_exam)
        # total = total
        if total >= 94:
            grade = Excellent
        elif total >= 88.5:
            grade = Superior
        elif total >= 83:
            grade = Meritorious
        elif total >= 77.5:
            grade = Very_Good
        elif total >= 72:
            grade = Good
        elif total >= 65.5:
            grade = Very_Satisfactory
        elif total >= 61:
            grade = Satisfactory
        elif total >= 55.5:
            grade = Fair
        elif total >= 50:
            grade = Passing
        elif total == " ":
            grade = Incomplete
        elif total < 50:
            grade = Failed
        else:
            grade = NG
        return grade

    # @staticmethod
    def get_comment(self, grade):
        if grade == Failed or grade == NG:
            comment = FAIL
        # elif grade == NG:
        #     comment = FAIL
        else:
            comment = PASS
        return comment

    def get_point(self, grade):
        p = 0
        # point = 0
        # for i in student:
        credit = self.course.credit
        if self.grade == Excellent:
            point = 1.00
        elif self.grade == Superior:
            point = 1.25
        elif self.grade == Meritorious:
            point = 1.50
        elif self.grade == Very_Good:
            point = 1.75
        elif self.grade == Good:
            point = 2.00
        elif self.grade == Very_Satisfactory:
            point = 2.25
        elif self.grade == Satisfactory:
            point = 2.50
        elif self.grade == Fair:
            point = 2.75
        elif self.grade == Passing:
            point = 3.00
        elif self.grade == Incomplete:
            point = 4.00
        else:
            point = 5.00
        p += int(credit) * point
        return p

    def calculate_gpa(self, total_credit_in_semester):
        current_semester = Semester.objects.get(is_current_semester=True)
        student = TakenCourse.objects.filter(student=self.student, course__status=self.student.status, course__semester=current_semester)
        p = 0
        point = 0
        for i in student:
            credit = i.course.credit
            if i.grade == Excellent:
                point = 1.00
            elif i.grade == Superior:
                point = 1.25
            elif i.grade == Meritorious:
                point = 1.50
            elif i.grade == Very_Good:
                point = 1.75
            elif i.grade == Good:
                point = 2.00
            elif i.grade == Very_Satisfactory:
                point = 2.25
            elif i.grade == Satisfactory:
                point = 2.50
            elif i.grade == Fair:
                point = 2.75
            elif i.grade == Passing:
                point = 3.00
            elif i.grade == Incomplete:
                point = 4.00
            else:
                point = 5.00
            p += int(credit) * point
        try:
            gpa = (p / total_credit_in_semester)
            return round(gpa, 2)
        except ZeroDivisionError:
            return 0
    
    def calculate_cgpa(self):
        current_semester = Semester.objects.get(is_current_semester=True)
        previousResult = Result.objects.filter(student__id=self.student.id, status__lt=self.student.status)
        previousCGPA = 0
        for i in previousResult:
            if i.cgpa is not None:
                previousCGPA += i.cgpa
        cgpa = 0
        if str(current_semester) == SECOND:
            first_sem_gpa = 0.0
            sec_sem_gpa = 0.0
            try:
                first_sem_result = Result.objects.get(student=self.student.id, semester=FIRST, status=self.student.status)
                first_sem_gpa += first_sem_result.gpa
            except:
                first_sem_gpa = 0

            try:
                sec_sem_result = Result.objects.get(student=self.student.id, semester=SECOND, status=self.student.status)
                sec_sem_gpa += sec_sem_result.gpa
            except:
                sec_sem_gpa = 0

            taken_courses = TakenCourse.objects.filter(student=self.student, student__status=self.student.status)
            TCC = 0
            TCP = 0
            for i in taken_courses:
                TCP += float(i.point)
            for i in taken_courses:
                TCC += int(i.course.credit)
            # cgpa = (first_sem_gpa + sec_sem_gpa) / 2

            print("TCP = ", TCP)
            print("TCC = ", TCC)
            print("first_sem_gpa = ", first_sem_gpa)
            print("sec_sem_gpa = ", sec_sem_gpa)
            print("cgpa = ", round(TCP / TCC, 2))

            try:
                cgpa = TCP / TCC
                return round(cgpa, 2)
            except ZeroDivisionError:
                return 0

            # return round(cgpa, 2)


class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    gpa = models.FloatField(null=True)
    cgpa = models.FloatField(null=True)
    semester = models.CharField(max_length=100, choices=SEMESTER)
    session = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=25, choices=STATUS, null=True)
