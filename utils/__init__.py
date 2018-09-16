import os
import logging
import yaml
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
            logging.debug(result_message)
    return result


def read_secrets(required_secrets):
    logging.debug("Reading secrets file...")
    with open("secrets.yaml", "r") as secrets_file:
        secrets_yaml = secrets_file.read()

    try:
        secrets = yaml.load(secrets_yaml)
    except yaml.YAMLError:
        logging.error("Error! Secrets YAML file invalid.")
    logging.debug("Checking secrets...")
    for (key, description) in required_secrets:
        try:
            secrets[key]
        except KeyError:
            message = "ERROR! Secret '{}' not found!\n  - Key description: {}"
            raise LookupError(message.format(key, description))
        logging.debug("  - '{}' set correctly.".format(key))
    return secrets


def checkout_branch(branch):
    try:
        result = run_shell(["git", "checkout", branch], display=False)
        logging.debug(result.stdout.decode("utf-8"))
    except subprocess.CalledProcessError:
        run_shell(["git", "checkout", "-b", branch])


def render_text(path, context):
    with open(os.path.join("../../", path), "r") as f:
        template_string = f.read()
    return Template(template_string).render(context)


def display_elapsed_time(start_time):
    mins = (timer() - start_time) // 60
    secs = (timer() - start_time) % 60
    logging.debug("Process took {:.0f}m {:.1f}s.\n".format(mins, secs))


def get_crowdin_api_key(project_name, secrets):
    allowed = set(ascii_uppercase)
    key = "".join(l for l in project_name.upper() if l in allowed)
    key += "_CROWDIN_API_KEY"
    logging.debug("Checking for secret '{}'".format(key))
    try:
        value = secrets[key]
        logging.debug("Found secret '{}'".format(key))
    except KeyError:
        message = "ERROR! Secret '{}' not found!"
        raise LookupError(message.format(key))
    return value

def git_reset():
    run_shell(["git", "reset", "--hard"])
    run_shell(["sudo", "git", "clean", "-fdx"])
