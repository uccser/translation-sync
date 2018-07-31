import os
import subprocess
import requests
from shutil import rmtree
from modules.utils import run, check_envs
from modules.crowdin_api import (
    upload_file_to_crowdin,
    create_crowdin_directory,
)
from repositories import REPOSITORIES

DEFAULT_WORKING_DIRECTORY = os.getcwd()
REPOSTIORY_DIRECTORY = "repositories"
GITHUB_BOT_EMAIL = "33709036+uccser-bot@users.noreply.github.com"
GITHUB_BOT_NAME = "UCCSER Bot"
BRANCH_PREFIX = "translation-"
REQUIRED_ENVIRONMENT_VARIABLES = [
    ["GITHUB_TOKEN", "OAuth token to use for GitHub API requests"],
]
MESSSAGE_FILE_TRIVAL_LINES = (
    '"POT-Creation-Date:',
    '"PO-Revision-Date:',
    "#: ",
)


def setup_git_account():
    """Set the name and email account of the git account."""
    run(["git", "config", "user.name", GITHUB_BOT_NAME])
    run(["git", "config", "user.email", GITHUB_BOT_EMAIL])


def clone_repository(repository_data):
    """Clone the repository, deleting any existing installations."""
    if os.path.isdir(repository_data["name"]):
        print("Existing repository detected! Deleting existing directory...")
        rmtree(repository_data["name"])
    run(["git", "clone", repository_data["git-address"]])


def start_docker_compose_system(repository_data):
    """Start the Docker Compose system."""
    run(repository_data["commands"]["start"])


def end_docker_compose_system(repository_data):
    """End the Docker Compose system."""
    run(repository_data["commands"]["end"])


def update_source_message_file(repository_data):
    pr_branch = BRANCH_PREFIX + "update-messages"
    target_branch = repository_data["branches"]["update-messages-target"]
    try:
        run(["git", "checkout", pr_branch])
    except subprocess.CalledProcessError:
        run(["git", "checkout", "-b", pr_branch])
    run(["git", "merge", "origin/" + target_branch, "--quiet", "--no-edit"])
    # TODO: Delete for release
    # run(["git", "reset", "HEAD", repository_data["django-message-file"]])
    run(repository_data["commands"]["makemessages"])
    run(["git", "add", repository_data["django-message-file"]])
    reset_message_file_comments(repository_data["django-message-file"])
    diff_result = run(["git", "diff", "--cached", "--quiet"], check=False)
    if diff_result.returncode == 1:
        print("Changes to source message file to push.")
        run(["git", "commit", "-m", "Update source language message file (django.po)"])
        run(["git", "push", "origin", pr_branch])
    else:
        print("No changes to source message file to push.")


def reset_message_file_comments(message_file_path):
    """Unstage any staged PO files that only have comment or date changes.

    This is achieved by checking the diff with HEAD, excluding any comment
    lines or lines starting with PO-Revision-Date or POT-Creation-Date.

    Must be run from the repository root directory.
    """
    previous = run(["git", "show", "HEAD:{}".format(message_file_path)], display=False).stdout.decode("utf-8")
    current = run(["git", "show", ":{}".format(message_file_path)], display=False).stdout.decode("utf-8")
    new_lines = list(set(current.split("\n")) - set(previous.split("\n")))
    unstage_message_file = True
    i = 0
    while unstage_message_file and i < len(new_lines):
        if not new_lines[i].startswith(MESSSAGE_FILE_TRIVAL_LINES):
            unstage_message_file = False
        i += 1
    if unstage_message_file:
        print("Message file '{}' only has trivial changes, unstaging file...".format(message_file_path))
        run(["git", "reset", "HEAD", message_file_path])


def push_source_files(repository_data):
    existing_directories = set()
    for source_directory in repository_data["source-directories"]:
        source_directory_segments = source_directory.rstrip("/").split("/")
        i = 1
        while i <= len(source_directory_segments):
            directory_path = os.path.join(*source_directory_segments[:i])
            if directory_path not in existing_directories:
                create_crowdin_directory(directory_path, repository_data)
                existing_directories.add(directory_path)
            i += 1

        for current_directory, directories, files in os.walk(source_directory):
            for directory in directories:
                directory_path = os.path.join(current_directory, directory)
                if directory_path not in existing_directories:
                    create_crowdin_directory(directory_path, repository_data)
                    existing_directories.add(directory_path)

            for filename in sorted(files):
                file_path = os.path.join(current_directory, filename)
                upload_file_to_crowdin(file_path, repository_data)


if __name__ == "__main__":
    check_envs(REQUIRED_ENVIRONMENT_VARIABLES)

    # Create directory for storing repostiories
    # if not os.path.exists(REPOSTIORY_DIRECTORY):
    #     os.makedirs(REPOSTIORY_DIRECTORY)
    os.chdir(REPOSTIORY_DIRECTORY)

    for repository_data in REPOSITORIES:
        # clone_repository(repository_data)
        os.chdir(repository_data["name"])
        # setup_git_account()
        # start_docker_compose_system(repository_data)
        # # Regenerate source langage (English) message files
        # update_source_message_file(repository_data)
        # Push source language (English) files) to Crowdin
        push_source_files(repository_data)
        # end_docker_compose_system(repository_data)
