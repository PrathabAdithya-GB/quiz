from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


# =====================
# CATEGORY
# =====================

class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


# =====================
# QUIZ
# =====================

class Quiz(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    overview = models.TextField(
        blank=True,
        help_text="Short overview shown on quiz detail page"
    )

    rules = models.TextField(
        blank=True,
        help_text="Quiz rules (time, attempts, marking)"
    )

    topics_covered = models.TextField(
        blank=True,
        help_text="Comma separated topics"
    )

    difficulty_label = models.CharField(
        max_length=50,
        blank=True,
        help_text="Easy / Medium / Hard / Mixed"
    )

    category = models.ForeignKey(
        Category,
        related_name="quizzes",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    time_limit = models.PositiveIntegerField(default=20)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# =====================
# QUESTION (ONLY ONE!)
# =====================

class Question(models.Model):

    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    quiz = models.ForeignKey(
        Quiz,
        related_name="questions",
        on_delete=models.CASCADE
    )
    text = models.TextField()
    marks = models.PositiveIntegerField(default=1)
    difficulty = models.CharField(
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default='easy'
    )

    def __str__(self):
        return self.text[:60]


# =====================
# CHOICE
# =====================

class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        related_name="choices",
        on_delete=models.CASCADE
    )
    text = models.CharField(max_length=300)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


# =====================
# ATTEMPT
# =====================

class Attempt(models.Model):
    user = models.ForeignKey(
        User,
        related_name="attempts",
        on_delete=models.CASCADE
    )
    quiz = models.ForeignKey(
        Quiz,
        related_name="attempts",
        on_delete=models.CASCADE
    )
    score = models.FloatField(default=0)
    total_marks = models.FloatField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.quiz} - {self.score}"


# =====================
# ANSWER
# =====================

class Answer(models.Model):
    attempt = models.ForeignKey(
        Attempt,
        related_name="answers",
        on_delete=models.CASCADE
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE
    )
    selected_choice = models.ForeignKey(
        Choice,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    is_correct = models.BooleanField(default=False)
    marks_awarded = models.FloatField(default=0)
