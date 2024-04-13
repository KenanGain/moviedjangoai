from django.urls import path
from . import views

urlpatterns = [
    path('',views.index, name='index'),
    path("search/",views.search, name="search"),
    path("movie/<int:id>/", views.view_detail, name="detail"),
    path("movie/<int:movie_id>/review/", views.review_page , name="review")
]
