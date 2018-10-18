import os
import logging
import glob
from zipfile import ZipFile
from shutil import copy
from utils import (
    checkout_branch,
    run_shell,
    git_reset,
    render_text,
)
from .crowdin_api import api_call, download_translations
from .constants import BRANCH_PREFIX, SOURCE_LANGUAGE
from .utils import (
    reset_message_file_comments,
    get_existing_files_at_head,
)

TRANSLATION_ZIP = "crowdin-translations.zip"
TEMPORARY_TRANSLATION_DIRECTORY = "project-translations"


def get_osx_locale_mapping(project):
    """Get dictionary mapping Crowdin language codes to osx_locale_codes.

    See https://support.crowdin.com/api/supported-languages/
    """
    response = api_call("supported-languages", project, json=True)
    languages_json = response.json()
    mapping = {
        language["crowdin_code"]: language["osx_locale"] for language in languages_json
    }
    # TODO: Language overrides
    return mapping


def get_project_languages(project):
    response = api_call("status", project, json=True)
    project_languages = response.json()
    active_languages = []
    for language in project_languages:
        if int(language["words_approved"]) > 0:
            active_languages.append(language["code"])
    return active_languages


def get_approved_files(language_status):
    approved_files = set()
    for node in language_status.get("files", list()):
        approved_files = approved_files.union(get_approved_node_files(node))
    return approved_files


def get_approved_node_files(node, parent_path=""):
    approved_files = set()
    node_path = os.path.join(parent_path, node["name"])
    if node["node_type"] == "file":
        is_approved_file = node["words"] == node["words_approved"]
        is_approved_message_file = node["name"].endswith(".po") and int(node["words_approved"]) > 0
        if is_approved_file or is_approved_message_file:
            approved_files.add(node_path)
    file_nodes = node.get("files", list())
    for file_node in file_nodes:
        approved_files = approved_files.union(get_approved_node_files(file_node, node_path))
    return approved_files


def copy_approved_files(project, extract_location, approved_files, language):
    source_path = os.sep + SOURCE_LANGUAGE + os.sep
    destination_path = os.sep + language + os.sep

    for approved_file in sorted(list(approved_files)):
        approved_file_destination = approved_file.replace(source_path, destination_path)
        source = os.path.join(
            extract_location,
            approved_file_destination
        )
        destination = os.path.join(
            project.directory,
            approved_file_destination
        )
        destination_directory = os.path.dirname(destination)
        if not os.path.exists(destination_directory):
            os.makedirs(destination_directory, exist_ok=True)
        try:
            copy(source, destination)
        except FileNotFoundError:
            logging.error("Could not copy file {}, it probably doesn't exist. Check if Crowdin has outdated files.".format(source))
        logging.info("Copied {}".format(approved_file_destination))


def pull_translations(project):
    locale_mapping = get_osx_locale_mapping(project)
    language_mapping_overrides = project.config["translation"]["language-mapping-overrides"]
    locale_mapping.update(language_mapping_overrides)
    project_languages = get_project_languages(project)

    # Download ZIP of translations
    download_translations(project, TRANSLATION_ZIP)
    extract_location = os.path.join(project.parent_directory, TEMPORARY_TRANSLATION_DIRECTORY)
    with ZipFile(TRANSLATION_ZIP, "r") as zipped_translations:
        zipped_translations.extractall(extract_location)
    os.remove(TRANSLATION_ZIP)

    for crowdin_language_code in project_languages:
        language = locale_mapping[crowdin_language_code]
        logging.info("Processing '{}' language...".format(language))
        target_branch = project.config["translation"]["branches"]["translation-target"]
        pr_branch = BRANCH_PREFIX + language
        checkout_branch(target_branch)
        checkout_branch(pr_branch)
        run_shell(["git", "merge", "origin/" + target_branch, "--quiet", "--no-edit"])
        response = api_call("language-status", project, json=True, language=crowdin_language_code)
        approved_files = get_approved_files(response.json())

        existing_files = get_existing_files_at_head()

        copy_approved_files(project, extract_location, approved_files, language)

        run_shell(["git", "add", "-A"])
        message_files = glob.glob("./**/{}/**/*.po".format(language), recursive=True)
        for message_file_path in message_files:
            if ("./" + message_file_path) in existing_files:
                reset_message_file_comments(message_file_path)
        diff_result = run_shell(["git", "diff", "--cached", "--quiet"], check=False)
        if diff_result.returncode == 1:
            logging.info("Changes to '{}' language to push.".format(language))
            run_shell(["git", "commit", "-m", "Update '{}' language translations".format(language)])
            run_shell(["git", "push", "origin", pr_branch])
            existing_pulls = project.repo.get_pulls(state="open", head="uccser:" + pr_branch, base=target_branch)
            if len(list(existing_pulls)) > 0:
                logging.info("Existing pull request detected.")
            else:
                context = {
                    "language": language,
                }
                header_text = render_text("translation/templates/pr-pull-translations-header.txt", context)
                body_text = render_text("translation/templates/pr-pull-translations-body.txt", context)
                pull = project.repo.create_pull(
                title=header_text,
                body=body_text,
                base=target_branch,
                head=pr_branch,
                )
                pull.add_to_labels("internationalization")
                logging.info("Pull request created: {} (#{})".format(pull.title, pull.number))
        else:
            logging.info("No changes to '{}' translation to push.".format(language))
        git_reset()
