"""Module for interacting with the Crowdin API."""

import os
import requests

API_URL = "https://api.crowdin.com/api/project/{project}/{method}"


def api_call(method, repository_data, files=None, **params):
    """Call a given api method and return response.

    Args:
        method: (str) API method to call
            (see https://support.crowdin.com/api/api-integration-setup/)
        params: (dict) API call arguments to encode in the url

    Returns:
        (str) Text content of the response
    """
    project = repository_data["name"]
    # params["key"] = os.environ[repository_data["crowdin-api-key"]]
    params["key"] = repository_data["crowdin-api-key"]
    response = requests.post(
        API_URL.format(project=project, method=method),
        files=files,
        params=params,
    )
    return response

#
# def api_call_text(method, **params):
#     """Call a given api method and return text content.
#
#     Args:
#         method: (str) API method to call
#             (see https://support.crowdin.com/api/api-integration-setup/)
#         params: (dict) API call arguments to encode in the url
#
#     Returns:
#         (str) Text content of the response
#     """
#     response = api_call(method, **params)
#     return response.text
#
#
# def api_call_xml(method, **params):
#     """Call a given api method and return XML tree.
#
#     Args:
#         method: (str) API method to call
#             (see https://support.crowdin.com/api/api-integration-setup/)
#         params: (dict) API call arguments to encode in the url
#
#     Returns:
#         lxml.etree object
#     """
#     response_text = api_call_text(method, **params)
#     xml = lxml.etree.fromstring(response_text.encode())
#     return xml
#
#
# def api_call_json(method, **params):
#     """Call a given api method and return JSON dictionary.
#
#     Args:
#         method: (str) API method to call
#             (see https://support.crowdin.com/api/api-integration-setup/)
#         params: (dict) API call arguments to encode in the url
#
#     Returns:
#         (dict) JSON dictionary
#     """
#     response = api_call(method, json=True, **params)
#     return response.json()


# --- API METHODS ---


def upload_file_to_crowdin(file_path, repository_data):
    files = {"files[{}]".format(file_path): open(file_path, "rb")}
    response = api_call("add-file", repository_data, files=files, json=True)
    response_data = response.json()
    if response.status_code == requests.codes.ok:
        print("{} - File uploaded to Crowdin.".format(file_path))
    elif response_data.get("error", dict()).get("code") == 5:
        response = api_call("update-file", repository_data, files=files, json=True)
        if response.status_code == requests.codes.ok:
            print("{} - File updated on Crowdin.".format(file_path))
    else:
        response.raise_for_status()


def create_crowdin_directory(directory, repository_data):
    response = api_call("add-directory", repository_data, name=directory, json=True)
    response_data = response.json()
    if response.status_code == requests.codes.ok:
        print("{} - Directory created on Crowdin.".format(directory))
    elif response_data.get("error", dict()).get("code") == 50:
        message = "{} - {}"
        print(message.format(directory, response_data["error"]["message"]))
    else:
        response.raise_for_status()
