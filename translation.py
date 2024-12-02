import os
import argparse

# Create argument parser
parser = argparse.ArgumentParser()
parser.add_argument("filename", help="Name of the input file")
args = parser.parse_args()

# Get the file extension
filename = args.filename
_, file_extension = os.path.splitext(filename)

# Determine which script to run based on the file extension
if file_extension == '.ass':
    script_to_run = 'ass_translation.py'
elif file_extension == '.srt':
    script_to_run = 'srt_translation.py'
else:
    print("Unsupported file type")
    exit()

# Read the script content
with open(script_to_run, 'r', encoding='utf-8') as file:
    script_content = file.read()

# Execute the script content
exec(script_content)