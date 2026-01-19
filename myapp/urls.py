from django.urls import path
from . import views

app_name = "myapp"

urlpatterns = [
    path("", views.index, name="index"),
    path("quizzes/", views.quiz_list, name="quiz_list"),
    path("quiz/<int:pk>/", views.quiz_detail, name="quiz_detail"),
    path("quiz/<int:pk>/take/", views.take_quiz, name="take_quiz"),
    path("quiz/<int:pk>/result/<int:attempt_id>/", views.result, name="result"),

    path("signup/", views.signup, name="signup"),
    path("profile/", views.profile, name="profile"),
    path("my-scores/", views.my_scores, name="my_scores"),

    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
]
