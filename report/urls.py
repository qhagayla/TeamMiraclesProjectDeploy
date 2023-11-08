from django.urls import path
from .views import *

urlpatterns = [

    path('<slug>/reports/', report_list, name='report_index'),

    path('progress/', view=ReportUserProgressView.as_view(), name='report_progress'),

    # path('marking/<int:pk>/', view=ReportMarkingList.as_view(), name='report_marking'),
    path('marking_list/', view=ReportMarkingList.as_view(), name='report_marking'),

    path('marking/<int:pk>/', view=ReportMarkingDetail.as_view(), name='report_marking_detail'),

    path('<int:pk>/<slug>/take/', view=ReportTake.as_view(), name='report_take'),

    path('<slug>/report_add/', ReportCreateView.as_view(), name='report_create'),
    path('<slug>/<int:pk>/add/', ReportUpdateView.as_view(), name='report_update'),
    path('<slug>/<int:pk>/delete/', report_delete, name='report_delete'),
    path('mc-question/add/<slug>/<int:report_id>/', MCQuestionCreate.as_view(), name='mc_create'),
    # path('mc-question/add/<int:pk>/<report_pk>/', MCQuestionCreate.as_view(), name='mc_create'),
]
