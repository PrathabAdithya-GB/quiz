import random
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.utils import timezone
from django.db.models import Count
from django.urls import reverse

from .models import Quiz, Question, Choice, Attempt, Answer, Category
from .forms import SignUpForm, EmailLoginForm

from django.db.models import Avg, Max

from .forms import ProfileUpdateForm
from django.contrib import messages

# =========================
# HOME PAGE
# =========================

def index(request):
    latest_quizzes = Quiz.objects.filter(is_published=True).order_by("-created_at")[:6]
    total_quizzes = Quiz.objects.filter(is_published=True).count()
    total_users = Attempt.objects.values("user").distinct().count()
    total_attempts = Attempt.objects.count()

    return render(request, "myapp/index.html", {
        "latest_quizzes": latest_quizzes,
        "total_quizzes": total_quizzes,
        "total_users": total_users,
        "total_attempts": total_attempts,
    })


# =========================
# QUIZ LIST
# =========================

def quiz_list(request):
    quizzes = Quiz.objects.filter(is_published=True)

    categories = (
        Category.objects
        .annotate(question_count=Count("quizzes__questions"))
        .filter(question_count__gte=1)
        .order_by("name")
    )

    return render(request, "myapp/quiz_list.html", {
        "quizzes": quizzes,
        "categories": categories,
    })
# =========================
# QUIZ DETAIL
# =========================

def quiz_detail(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, is_published=True)
    return render(request, "myapp/quiz_detail.html", {"quiz": quiz})


# =========================
# TAKE QUIZ (MULTI-CORRECT + SAFE)
# =========================

@login_required
def take_quiz(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, is_published=True)

    questions = list(
        quiz.questions.prefetch_related("choices")
    )

    selected_questions = random.sample(questions, min(20, len(questions)))

    # Attach correct_count (used in template)
    for q in selected_questions:
        q.correct_count = q.choices.filter(is_correct=True).count()

    if request.method == "POST":
        attempt = Attempt.objects.create(
            user=request.user,
            quiz=quiz,
            started_at=timezone.now(),
            total_marks=sum(q.marks for q in selected_questions),
        )

        score = 0

        for q in selected_questions:
            selected_ids = request.POST.getlist(f"question_{q.id}")
            selected_ids = set(map(int, selected_ids)) if selected_ids else set()

            correct_ids = set(
                q.choices.filter(is_correct=True).values_list("id", flat=True)
            )

            # ❌ Unanswered
            if not selected_ids:
                is_correct = False
                marks_awarded = 0

            # ❌ Any wrong option selected
            elif not selected_ids.issubset(correct_ids):
                is_correct = False
                marks_awarded = 0

            # ✅ All correct selected
            elif selected_ids == correct_ids:
                is_correct = True
                marks_awarded = q.marks

            # 🟡 Partial correct (multi-correct only)
            else:
                is_correct = False
                marks_awarded = round(
                    q.marks * (len(selected_ids) / len(correct_ids)), 2
                )

            Answer.objects.create(
                attempt=attempt,
                question=q,
                is_correct=is_correct,
                marks_awarded=marks_awarded,
            )

            score += marks_awarded

        attempt.score = score
        attempt.completed_at = timezone.now()
        attempt.save()

        return redirect(
            "myapp:result",
            pk=quiz.id,
            attempt_id=attempt.id,
        )

    return render(request, "myapp/take_quiz.html", {
        "quiz": quiz,
        "questions": selected_questions,
    })


@login_required
def result(request, pk, attempt_id):
    attempt = get_object_or_404(
        Attempt,
        id=attempt_id,
        user=request.user,
        quiz_id=pk
    )

    answers = attempt.answers.select_related("question")

    return render(request, "myapp/result.html", {
        "attempt": attempt,
        "answers": answers,
    })


# =========================
# LEADERBOARD
# =========================




# =========================
# AUTH – EMAIL LOGIN
# =========================

def login_view(request):
    next_url = request.GET.get("next") or reverse("myapp:index")

    if request.method == "POST":
        form = EmailLoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect(next_url)
    else:
        form = EmailLoginForm()

    return render(request, "registration/login.html", {
        "form": form,
        "next": next_url,
    })


def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("myapp:index")
    else:
        form = SignUpForm()

    return render(request, "registration/signup.html", {
        "form": form
    })


# =========================
# STATIC PAGES
# =========================

def about(request):
    return render(request, "myapp/about.html")


def contact(request):
    return render(request, "myapp/contact.html")

@login_required
def profile(request):
    attempts = Attempt.objects.filter(user=request.user, completed_at__isnull=False)

    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("myapp:profile")
    else:
        form = ProfileUpdateForm(instance=request.user)

    context = {
        "form": form,
        "total_attempts": attempts.count(),
        "avg_score": attempts.aggregate(avg=Avg("score"))["avg"] or 0,
        "best_score": attempts.aggregate(max=Max("score"))["max"] or 0,
        "recent_attempts": attempts.order_by("-completed_at")[:5],
    }

    return render(request, "myapp/profile.html", context)


@login_required
def my_scores(request):
    attempts = Attempt.objects.filter(user=request.user).order_by("-completed_at")
    return render(request, "myapp/my_scores.html", {
        "attempts": attempts,
    })