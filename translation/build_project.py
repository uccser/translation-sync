from .crowdin_api import API_URL
import requests


def build_project(project):
    print("Triggering build of translations for {}...".format(project.name))
    url = API_URL.format(project=project.name, method="export")
    url += "?key={key}".format(key=project.crowdin_api_key)
    run_shell(["curl", url])
