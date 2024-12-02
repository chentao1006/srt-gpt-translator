# -*- coding: utf-8 -*-

import re
import openai
from tqdm import tqdm
import os
import json
import chardet
import configparser
import argparse

# Load settings from config file
with open('settings.cfg', 'rb') as f:
    content = f.read()
    encoding = chardet.detect(content)['encoding']

with open('settings.cfg', encoding=encoding) as f:
    config_text = f.read()
    config = configparser.ConfigParser()
    config.read_string(config_text)

# Get OpenAI API key and target language
openai_url = config.get('option', 'openai-url')
openai_apikey = config.get('option', 'openai-apikey')
language_name = config.get('option', 'target-language')

# Set OpenAI API key
openai.api_base = openai_url
openai.api_key = openai_apikey

# Create argument parser
parser = argparse.ArgumentParser()
parser.add_argument("filename", help="Name of the input file")
parser.add_argument("--test", help="Only translate the first 3 lines", action="store_true")
args = parser.parse_args()

# Get command line arguments
filename = args.filename
base_filename, file_extension = os.path.splitext(filename)
new_filenametxt = base_filename + "_translated.ass"
new_filenametxt2 = base_filename + "_translated_bilingual.ass"

jsonfile = base_filename + "_process.json"
# Load already translated texts from file
translated_dict = {}
try:
    with open(jsonfile, "r", encoding="utf-8") as f:
        translated_dict = json.load(f)
except FileNotFoundError:
    pass

def is_translation_valid(original_text, translated_text):
    if "\n" in translated_text:
        print(original_text)
        print(translated_text)
        return False
    return True

def translate_text(text):
    max_retries = 10
    retries = 0
    
    while retries < max_retries:
        try:
            completion = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"Translate the following subtitle text into {language_name}. Please pay attention to the context to make whole dialog consistent. Use natural language and avoid word-for-word translation. DO NOT add line break. Make all text in one line.",
                    },
                    {
                        "role": "user",
                        "content": text,
                    }
                ],
            )
            t_text = (
                completion["choices"][0]
                .get("message")
                .get("content")
                .encode("utf8")
                .decode()
            )
            
            if is_translation_valid(text, t_text):
                return t_text
            else:
                retries += 1
                print(f"Invalid translation format. Retrying ({retries}/{max_retries})")
        
        except Exception as e:
            import time
            sleep_time = 60
            time.sleep(sleep_time)
            retries += 1
            print(e, f"will sleep {sleep_time} seconds, Retrying ({retries}/{max_retries})")

    print(f"Unable to get a valid translation after {max_retries} retries. Returning the original text.")
    return text
    
def translate_and_store(text):
    if text in translated_dict:
        return translated_dict[text]

    translated_text = translate_text(text)
    translated_dict[text] = translated_text

    with open(jsonfile, "w", encoding="utf-8") as f:
        json.dump(translated_dict, f, ensure_ascii=False, indent=4)

    return translated_text 

if filename.endswith('.ass'):
    with open(filename, 'r', encoding='utf-8') as file:
        lines = file.readlines()
else:
    print("Unsupported file type")
    exit()

translated_lines = []

for line in tqdm(lines):
    if line.startswith("Dialogue:"):
        dialogue_parts = line.split(",", 9)
        original_text = dialogue_parts[9]
        translated_text = translate_and_store(original_text)
        dialogue_parts[9] = translated_text
        translated_line = ",".join(dialogue_parts)
        translated_lines.append(translated_line)
    else:
        translated_lines.append(line)

with open(new_filenametxt, "w", encoding="utf-8") as f:
    f.writelines(translated_lines)

bilingual_lines = []

for line in tqdm(lines):
    if line.startswith("Dialogue:"):
        dialogue_parts = line.split(",", 9)
        original_text = dialogue_parts[9]
        translated_text = translate_and_store(original_text)
        bilingual_text = f"{translated_text}\\N{original_text}"
        dialogue_parts[9] = bilingual_text
        bilingual_line = ",".join(dialogue_parts)
        bilingual_lines.append(bilingual_line)
    else:
        bilingual_lines.append(line)

with open(new_filenametxt2, "w", encoding="utf-8") as f:
    f.writelines(bilingual_lines)

try:
    os.remove(jsonfile)
    print(f"File '{jsonfile}' has been deleted.")
except FileNotFoundError:
    print(f"File '{jsonfile}' not found. No file was deleted.")