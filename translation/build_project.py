import logging
from .crowdin_api import API_URL
from utils import run_shell


def build_project(project):
    logging.debug("Triggering build of translations for {}...".format(project.name))
    url = API_URL.format(project=project.name, method="export")
    url += "?key={key}".format(key=project.crowdin_api_key)
    run_shell(["curl", url])
