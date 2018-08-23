from .crowdin_api import API_URL
import requests


def build_project(project):
    params = {
        "key": project.crowdin_api_key,
        "json": True,
    }
    response = requests.get(
        API_URL.format(project=project.name, method="export"),
        params=params,
        stream=True,
    )
    response_data = response.json()
    print(response_data)
    return response_data
