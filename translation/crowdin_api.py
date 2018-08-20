"""Module for interacting with the Crowdin API."""

import requests
import os.path

API_URL = "https://api.crowdin.com/api/project/{project}/{method}"


def api_call(method, project, files=None, **params):
    """Call a given api method and return response.

    Args:
        method: (str) API method to call
            (see https://support.crowdin.com/api/api-integration-setup/)
        params: (dict) API call arguments to encode in the url

    Returns:
        (str) Text content of the response
    """
    params["key"] = project.crowdin_api_key
    response = requests.post(
        API_URL.format(project=project.name, method=method),
        files=files,
        params=params,
    )
    return response


# --- API METHODS ---


def upload_file_to_crowdin(file_path, project):
    export_pattern = file_path.replace("/en/", "/%osx_locale%/")
    files = {
        "files[{}]".format(file_path): (os.path.basename(file_path), open(file_path, "rb").read()),
        "export_patterns[{}]".format(file_path): (None, export_pattern),
    }
    response = api_call(
        "add-file",
        project,
        files=files,
        json=True
    )
    response_data = response.json()
    if response.status_code == requests.codes.ok:
        print("{} - File uploaded to Crowdin.".format(file_path))
    elif response_data.get("error", dict()).get("code") == 5:
        response = api_call(
            "update-file",
            project,
            files=files,
            json=True
        )
        if response.status_code == requests.codes.ok:
            print("{} - File updated on Crowdin.".format(file_path))
    else:
        print(response)
        print(response.json())
        response.raise_for_status()


def create_crowdin_directory(directory, project):
    response = api_call("add-directory", project, name=directory, json=True)
    response_data = response.json()
    if response.status_code == requests.codes.ok:
        print("{} - Directory created on Crowdin.".format(directory))
    elif response_data.get("error", dict()).get("code") == 50:
        message = "{} - {}"
        print(message.format(directory, response_data["error"]["message"]))
    else:
        response.raise_for_status()


def download_translations(project, translation_zip):
    print("Downloading translations to {}".format(translation_zip))
    params = {"key": project.crowdin_api_key}
    response = requests.get(
        API_URL.format(project=project.name, method="download/all.zip"),
        params=params,
    )
    with open(translation_zip, "wb") as f:
        f.write(response.content)
    print("Download complete.")
