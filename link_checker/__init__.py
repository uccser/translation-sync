from linkie import Linkie
from utils import render_text


def check_links(project):
    """ """
    linkie_config = project.config.get("broken-link-checker", dict())
    checker = Linkie(config=linkie_config)
    result = checker.run()
    print()

    broken_links = dict()
    for url, url_data in checker.urls.items():
        if url_data['broken']:
            broken_links[url] = url_data

    context = {
        "broken_links": broken_links,
        "number_files": checker.file_count,
    }

    header_text = render_text("link_checker/templates/issue-broken-links-header.txt", context)
    body_text = render_text("link_checker/templates/issue-broken-links-body.txt", context)

    bot_issues = project.repo.get_issues(creator=project.bot)
    existing_issue = None
    for issue in bot_issues:
        if "broken link" in issue.title:
            existing_issue = issue

    # If existing issue and no errors, close issue
    if existing_issue and not result:
        message = "Closing existing issue, as link checker now detects no broken links."
        print(message)
        existing_issue.create_comment(message)
        existing_issue.edit(state="closed")
    # Else if existing issue and errors
    elif existing_issue and result:
        print("Checking if existing issue matches result.")
        if header_text == existing_issue.title and body_text == existing_issue.body:
            print("Existing issue is up to date.")
        else:
            message = "Updating issue to match latest broken link checker results."
            print(message)
            existing_issue.edit(title=header_text, body=body_text)
            existing_issue.create_comment(message)
    # Else if no existing issue and errors, create issue
    elif not existing_issue and result:
        issue = project.repo.create_issue(
            title=header_text,
            body=body_text,
        )
        issue.add_to_labels("bug")
