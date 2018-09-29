"""Modules used in translating repositories."""

import logging
from utils import (
    run_shell,
    checkout_branch,
    git_reset,
    render_text,
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
    message_files = translation_data["django-message-file"]
    if not isinstance(message_files, list):
        message_files = [message_files]
    for message_file in message_files:
        run_shell(["git", "add", message_file])
        reset_message_file_comments(message_file)
    diff_result = run_shell(["git", "diff", "--cached", "--quiet"], check=False)
    if diff_result.returncode == 1:
        logging.info("Changes to source message files to push.")
        run_shell(["git", "commit", "-m", "Update source language message files"])
        run_shell(["git", "push", "origin", pr_branch])
        existing_pulls = project.repo.get_pulls(state="open", head="uccser:" + pr_branch, base=target_branch)
        if len(list(existing_pulls)) > 0:
            logging.info("Existing pull request detected.")
        else:
            context = {
                "message_files": message_files,
            }
            header_text = render_text(
                "translation/templates/pr-update-source-messages-header.txt",
                context
            )
            body_text = render_text(
                "translation/templates/pr-update-source-messages-body.txt",
                context
            )
            pull = project.repo.create_pull(
                title=header_text,
                body=body_text,
                base=target_branch,
                head=pr_branch,
            )
            pull.add_to_labels("internationalization")
            logging.info("Pull request created: {} (#{})".format(pull.title, pull.number))
    else:
        logging.info("No changes to source message files to push.")
    git_reset()
