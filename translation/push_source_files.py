"""Modules used in translating repositories."""

import os
from .crowdin_api import (
    upload_file_to_crowdin,
    create_crowdin_directory,
)
from .constants import SOURCE_LANGUAGE
from utils import git_reset


def push_source_files(project):
    translation_data = project.config["translation"]
    existing_directories = set()
    valid_file_types = tuple(translation_data["file-types"])

    for source_directory_path in translation_data["source-directories"]:
        source_directory = source_directory_path.format(language=SOURCE_LANGUAGE)
        source_directory_segments = source_directory.rstrip("/").split("/")
        i = 1
        while i <= len(source_directory_segments):
            directory_path = os.path.join(*source_directory_segments[:i])
            if directory_path not in existing_directories:
                create_crowdin_directory(directory_path, project)
                existing_directories.add(directory_path)
            i += 1

        for current_directory, directories, files in os.walk(source_directory):
            for directory in sorted(directories):
                directory_path = os.path.join(current_directory, directory)
                if directory_path not in existing_directories:
                    create_crowdin_directory(directory_path, project)
                    existing_directories.add(directory_path)

            for filename in sorted(files):
                if filename.endswith(valid_file_types):
                    file_path = os.path.join(current_directory, filename)
                    upload_file_to_crowdin(file_path, project)
    git_reset()
