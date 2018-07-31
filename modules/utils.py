import os
import subprocess


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
