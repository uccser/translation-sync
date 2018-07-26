import os
import subprocess
from shutil import rmtree

DEFAULT_WORKING_DIRECTORY = os.getcwd()
REPOSTIORY_DIRECTORY = "repositories"
GITHUB_BOT_EMAIL = "33709036+uccser-bot@users.noreply.github.com"
GITHUB_BOT_NAME = "UCCSER Bot"
BRANCH_PREFIX = "translation-"
REPOSITORIES = [
    {
        "title": "CS Unplugged",
        "name": "cs-unplugged",
        "git-address": "git@github.com:uccser/cs-unplugged.git",
        "crowdin-config-file": "crowdin_content.yaml",
        "django-message-file": "csunplugged/locale/en/LC_MESSAGES/django.po",
        "commands": {
            "start": [
                ["./csu", "start"],
                ["./csu", "update"],
            ],
            "end": ["./csu", "end"],
            "makemessages": ["./csu", "dev", "makemessages"],
        },
        "branches": {
            # Branch for upload of source content to Crowdin
            "translation-source": "develop",
            # Branch that new translations will be merged into
            "translation-target": "develop",
            # Branch that updated English message PO files will be merged into
            "update-messages-target": "develop",
            # Branch that new metadata for in context localisation will be merged into
            "in-context-target": "develop",
            # Code for in-context localisation pseudo language on Crowdin
            "in-context-pseudo-language-crowdin": "en-UD",
            # Code for in-context localisation pseudo language on website
            "in-context-pseudo-language-website": "xx_LR",
        },
    },
]
REQUIRED_ENVIRONMENT_VARIABLES = [
    ["GITHUB_TOKEN", "OAuth token to use for GitHub API requests"],
]
MESSSAGE_FILE_TRIVAL_LINES = (
    '"POT-Creation-Date:',
    '"PO-Revision-Date:',
    "#: ",
)


def run(commands, display=True, check=True):
    """Run a list of shell commands.

    Args:
        commands (list of strings OR list of lists of strings).
    """
    if not all(isinstance(command, list) for command in commands):
        commands = [commands]
    for command in commands:
        result = subprocess.run(command, check=check, stdout=subprocess.PIPE)
        result_message = result.stdout.decode("utf-8")
        if display and result_message:
            print(result_message)
    return result


def check_envs():
    print("Checking environment variables...")
    for (key, description) in REQUIRED_ENVIRONMENT_VARIABLES:
        try:
            os.environ[key]
        except KeyError:
            message = "ERROR! Enviornment variable '{}' not found!\n  - Key description: {}"
            raise LookupError(message.format(key, description))
        print("  - '{}' set correctly.".format(key))
    print()


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


if __name__ == "__main__":
    check_envs()

    # Create directory for storing repostiories
    if not os.path.exists(REPOSTIORY_DIRECTORY):
        os.makedirs(REPOSTIORY_DIRECTORY)
    os.chdir(REPOSTIORY_DIRECTORY)

    for repository_data in REPOSITORIES:
        clone_repository(repository_data)
        os.chdir(repository_data["name"])
        setup_git_account()
        start_docker_compose_system(repository_data)
        update_source_message_file(repository_data)
        end_docker_compose_system(repository_data)
