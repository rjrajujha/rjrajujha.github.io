from django.views.generic import TemplateView

from apps.contact.forms import ContactForm
from apps.projects.models import Project

from .content import ABOUT_POINTS, EXPERIENCE_ITEMS, PROFILE, SKILL_GROUPS, TESTIMONIALS


class HomePageView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "profile": PROFILE,
                "about_points": ABOUT_POINTS,
                "skill_groups": SKILL_GROUPS,
                "experience_items": EXPERIENCE_ITEMS,
                "testimonials": TESTIMONIALS,
                "featured_projects": Project.objects.filter(is_featured=True)[:6],
                "contact_form": ContactForm(),
            }
        )
        return context
