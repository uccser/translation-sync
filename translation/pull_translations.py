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
    LANGUAGE_MAPPING_OVERRIDES,
)

TRANSLATION_ZIP = "crowdin-translations.zip"
TEMPORARY_TRANSLATION_DIRECTORY = "project-translations"


def get_language_mapping(project):
    """Get dictionary mapping Crowdin language codes to osx_locale_codes.

    See https://support.crowdin.com/api/supported-languages/

    Returns:
        Dictionary mapping Crowdin language code to OSX locale codes.
    """
    response = api_call("supported-languages", project, json=True)
    languages_json = response.json()
    languages = dict()
    for language in languages_json:
        crowdin_code = language["crowdin_code"]
        osx_locale = language["osx_locale"]
        django_code = LANGUAGE_MAPPING_OVERRIDES.get(crowdin_code, osx_locale)
        languages[crowdin_code] = {
            "osx_locale": osx_locale,
            "django_code": django_code,
        }
    return languages


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


def copy_approved_files(project, extract_location, approved_files, source_language, destination_language):
    approved_path = os.sep + SOURCE_LANGUAGE + os.sep
    source_path = os.sep + source_language + os.sep
    destination_path = os.sep + destination_language + os.sep

    for approved_file in sorted(list(approved_files)):
        approved_file_source = approved_file.replace(approved_path, source_path)
        approved_file_destination = approved_file.replace(approved_path, destination_path)
        source = os.path.join(
            extract_location,
            approved_file_source
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
            logging.info("Copied {}".format(approved_file_destination))
        except FileNotFoundError:
            logging.error("Could not copy file {} to {}, it probably doesn't exist. Check if Crowdin has outdated files.".format(source, destination))

    # Check file overrides
    override_filenames = project.config["translation"].get("file-overrides", list())
    for override_filename in override_filenames:
        source = os.path.join(
            project.directory,
            override_filename
        )
        destination = os.path.join(
            project.directory,
            override_filename.replace(approved_path, destination_path)
        )
        destination_directory = os.path.dirname(destination)
        if not os.path.exists(destination_directory):
            os.makedirs(destination_directory, exist_ok=True)
        copy(source, destination)
        # If YAML file, append YAML header (we don't store these in our repo)
        YAML_HEADER = "---\n"
        if destination.endswith('.yaml'):
            with open(destination, "r+") as f:
                current_contents = f.read()
                if not current_contents.startswith(YAML_HEADER):
                    f.seek(0)
                    f.write(YAML_HEADER + current_contents)
        logging.info("Copied {} (set by override)".format(approved_file_destination))


def pull_translations(project):
    locale_mapping = get_language_mapping(project)
    project_languages = get_project_languages(project)

    # Download ZIP of translations
    download_translations(project, TRANSLATION_ZIP)
    extract_location = os.path.join(project.parent_directory, TEMPORARY_TRANSLATION_DIRECTORY)
    with ZipFile(TRANSLATION_ZIP, "r") as zipped_translations:
        zipped_translations.extractall(extract_location)
    os.remove(TRANSLATION_ZIP)

    for crowdin_language_code in project_languages:
        source_language = locale_mapping[crowdin_language_code]["osx_locale"]
        destination_language = locale_mapping[crowdin_language_code]["django_code"]
        logging.info("Processing '{}' language...".format(destination_language))
        target_branch = project.config["translation"]["branches"]["translation-target"]
        pr_branch = BRANCH_PREFIX + destination_language
        checkout_branch(target_branch)
        checkout_branch(pr_branch)
        run_shell(["git", "merge", "origin/" + target_branch, "--quiet", "--no-edit"])
        response = api_call("language-status", project, json=True, language=crowdin_language_code)
        approved_files = get_approved_files(response.json())

        existing_files = get_existing_files_at_head()
        copy_approved_files(project, extract_location, approved_files, source_language, destination_language)

        run_shell(["git", "add", "-A"])
        message_files = glob.glob("./**/{}/**/*.po".format(destination_language), recursive=True)
        for message_file_path in message_files:
            if message_file_path[2:] in existing_files:
                reset_message_file_comments(message_file_path)
        diff_result = run_shell(["git", "diff", "--cached", "--quiet"], check=False)
        if diff_result.returncode == 1:
            logging.info("Changes to ({}/{}) language to push.".format(source_language, destination_language))
            run_shell(["git", "commit", "-m", "Update '{}' language translations".format(destination_language)])
            run_shell(["git", "push", "origin", pr_branch])
            existing_pulls = project.repo.get_pulls(state="open", head="uccser:" + pr_branch, base=target_branch)
            if len(list(existing_pulls)) > 0:
                logging.info("Existing pull request detected.")
            else:
                context = {
                    "language": destination_language,
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
            logging.info("No changes to ({}/{}) translation to push.".format(source_language, destination_language))
        git_reset()
