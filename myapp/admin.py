from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.urls import path
from django.utils.html import format_html
from django.http import HttpResponse
from django.core.cache import cache

import uuid

from .models import Category, Quiz, Question, Choice, Attempt, Answer
from myapp.forms import ExcelUploadForm
from myapp.utils.excel_importer import parse_excel, import_parsed_data
from myapp.utils.excel_template import generate_template


# =============================
# INLINE CONFIGURATIONS
# =============================

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1


# =============================
# CATEGORY ADMIN
# =============================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


# =============================
# QUIZ ADMIN + EXCEL TOOLS
# =============================

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "is_published", "time_limit", "excel_tools")
    list_filter = ("is_published",)
    search_fields = ("title",)

    fieldsets = (
        ("Basic Info", {
            "fields": ("title", "description", "is_published")
        }),
        ("Quiz Content (Shown to Users)", {
            "fields": (
                "overview",
                "topics_covered",
                "rules",
                "difficulty_label",
                "time_limit",
            )
        }),
    )

    # -----------------------------
    # CUSTOM ADMIN URLS
    # -----------------------------
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "upload-excel/",
                self.admin_site.admin_view(self.upload_excel),
                name="quiz_upload_excel",
            ),
            path(
                "confirm-import/",
                self.admin_site.admin_view(self.confirm_import),
                name="quiz_confirm_import",
            ),
            path(
                "download-template/",
                self.admin_site.admin_view(self.download_template),
                name="quiz_download_template",
            ),
        ]
        return custom_urls + urls

    # -----------------------------
    # EXCEL ACTION BUTTONS
    # -----------------------------
    def excel_tools(self, obj):
        return format_html(
            '<a class="button" href="upload-excel/">Upload Excel</a>&nbsp;'
            '<a class="button" href="download-template/">Download Template</a>'
        )
    excel_tools.short_description = "Excel Tools"

    # =====================================================
    # STEP 1 — UPLOAD & PREVIEW (CACHE-BASED)
    # =====================================================
    def upload_excel(self, request):
        if request.method == "POST":
            form = ExcelUploadForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    parsed_data = parse_excel(request.FILES["file"])

                    cache_key = f"excel_preview_{uuid.uuid4()}"
                    cache.set(cache_key, parsed_data, timeout=600)

                    request.session["excel_preview_key"] = cache_key

                    return render(
                        request,
                        "admin/excel_preview.html",
                        {"data": parsed_data},
                    )

                except Exception as e:
                    messages.error(request, str(e))
        else:
            form = ExcelUploadForm()

        return render(
            request,
            "admin/upload_excel.html",
            {"form": form, "title": "Upload Quiz via Excel"},
        )

    # =====================================================
    # STEP 2 — CONFIRM & IMPORT
    # =====================================================
    def confirm_import(self, request):
        cache_key = request.session.get("excel_preview_key")

        if not cache_key:
            messages.error(request, "Preview expired. Please upload again.")
            return redirect("../")

        parsed_data = cache.get(cache_key)

        if not parsed_data:
            messages.error(request, "Preview data not found.")
            return redirect("../")

        try:
            import_parsed_data(parsed_data)

            cache.delete(cache_key)
            del request.session["excel_preview_key"]

            messages.success(request, "Quiz imported successfully!")

        except Exception as e:
            messages.error(request, f"Import failed: {e}")

        return redirect("../")

    # =====================================================
    # DOWNLOAD TEMPLATE
    # =====================================================
    def download_template(self, request):
        wb = generate_template()
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="quiz_template.xlsx"'
        wb.save(response)
        return response


# =============================
# QUESTION ADMIN
# =============================

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "quiz", "difficulty", "marks")
    list_filter = ("difficulty", "quiz")
    search_fields = ("text",)
    inlines = [ChoiceInline]


# =============================
# OTHER MODELS
# =============================

@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ("text", "question", "is_correct")
    list_filter = ("is_correct",)
    search_fields = ("text",)


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "quiz", "score", "total_marks", "completed_at")
    list_filter = ("quiz",)
    search_fields = ("user__username",)


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("attempt", "question", "is_correct", "marks_awarded")
    list_filter = ("is_correct",)
