import re
import os


def remove_dashes_in_image_names(input_file):
    pattern = re.compile(r"(\d+)\s+(ms-\d+_\d+\.jpg)$")
    updated_lines = []

    with open(input_file, "r") as file:
        for line in file:
            match = pattern.match(line)
            if match:
                number = match.group(1)
                image_name = match.group(2)
                updated_line = f"{number} {image_name.replace('-', '')}"
                updated_lines.append(updated_line)
            else:
                updated_lines.append(line.rstrip("\n"))

    with open(input_file, "w") as file:
        file.write("\n".join(updated_lines))


def process_files_in_directory(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            file_path = os.path.join(directory, filename)
            remove_dashes_in_image_names(file_path)


# Example usage
directory = (
    "../app/mediafiles/manuscripts/annotation/"  # Replace with your directory path
)
process_files_in_directory(directory)
