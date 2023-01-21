# from django.shortcuts import render
from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    template_name = 'about/author.html'
    # return render('')


class AboutTechView(TemplateView):
    template_name = 'about/tech.html'
