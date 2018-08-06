"""Modules used in translating repositories."""

from utils import (
    run_shell,
    checkout_branch,
    git_reset,
)
from .constants import BRANCH_PREFIX
from .utils import reset_message_file_comments


def update_source_message_file(project):
    translation_data = project.config["translation"]
    target_branch = translation_data["branches"]["update-messages-target"]
    pr_branch = BRANCH_PREFIX + "update-messages"
    checkout_branch(pr_branch)
    run_shell(["git", "merge", "origin/" + target_branch, "--quiet", "--no-edit"])
    run_shell(translation_data["commands"]["start"])
    run_shell(translation_data["commands"]["makemessages"])
    run_shell(translation_data["commands"]["end"])
    run_shell(["git", "add", translation_data["django-message-file"]])
    reset_message_file_comments(translation_data["django-message-file"])
    diff_result = run_shell(["git", "diff", "--cached", "--quiet"], check=False)
    if diff_result.returncode == 1:
        print("Changes to source message file to push.")
        run_shell(["git", "commit", "-m", "Update source language message file (django.po)"])
        run_shell(["git", "push", "origin", pr_branch])
    else:
        print("No changes to source message file to push.")
    git_reset()