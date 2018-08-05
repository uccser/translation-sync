import os
import subprocess
from jinja2 import Template
from timeit import default_timer as timer
from string import ascii_uppercase


def run_shell(commands, display=True, check=True):
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


def check_envs(envs):
    print("Checking environment variables...")
    for (key, description) in envs:
        try:
            os.environ[key]
        except KeyError:
            message = "ERROR! Enviornment variable '{}' not found!\n  - Key description: {}"
            raise LookupError(message.format(key, description))
        print("  - '{}' set correctly.".format(key))
    print()


def checkout_branch(branch):
    try:
        result = run_shell(["git", "checkout", branch], display=False)
        print(result.stdout.decode("utf-8"))
    except subprocess.CalledProcessError:
        run_shell(["git", "checkout", "-b", branch])


def render_text(path, context):
    with open(os.path.join("../../", path), "r") as f:
        template_string = f.read()
    return Template(template_string).render(context)


def display_elapsed_time(start_time):
    mins = (timer() - start_time) // 60
    secs = (timer() - start_time) % 60
    print("Process took {:.0f}m {:.1f}s.\n".format(mins, secs))


def get_crowdin_api_key(project_name):
    allowed = set(ascii_uppercase)
    key = "".join(l for l in project_name.upper() if l in allowed)
    key += "_CROWDIN_API_KEY"
    try:
        value = os.environ[key]
    except KeyError:
        message = "ERROR! Enviornment variable '{}' not found!"
        raise LookupError(message.format(key))
    return value
