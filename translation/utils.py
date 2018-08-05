from utils import run_shell

MESSSAGE_FILE_TRIVAL_LINES = (
    '"POT-Creation-Date:',
    '"PO-Revision-Date:',
    "#: ",
)


def reset_message_file_comments(message_file_path):
    """Unstage any staged PO files that only have comment or date changes.

    This is achieved by checking the diff with HEAD, excluding any comment
    lines or lines starting with PO-Revision-Date or POT-Creation-Date.

    Must be run from the repository root directory.
    """
    previous = run_shell(["git", "show", "HEAD:{}".format(message_file_path)], display=False).stdout.decode("utf-8")
    current = run_shell(["git", "show", ":{}".format(message_file_path)], display=False).stdout.decode("utf-8")
    new_lines = list(set(current.split("\n")) - set(previous.split("\n")))
    unstage_message_file = True
    i = 0
    while unstage_message_file and i < len(new_lines):
        if not new_lines[i].startswith(MESSSAGE_FILE_TRIVAL_LINES):
            unstage_message_file = False
        i += 1
    if unstage_message_file:
        print("Message file '{}' only has trivial changes, unstaging file...".format(message_file_path))
        run_shell(["git", "reset", "HEAD", message_file_path])
