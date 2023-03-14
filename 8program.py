import os
import re
import pypandoc
from gtts import gTTS
import argparse
from pydub import AudioSegment

# define the regular expression for detecting questions and answers
question_regex = re.compile(r'^#\s*(.*)$')
answer_regex = re.compile(r'^\s*-\s*(.*)$')

# define the language for the TTS voice (change if necessary)
language = 'de'

# create an argument parser to accept the list of files as a command line argument
parser = argparse.ArgumentParser()
parser.add_argument('files', metavar='file', type=str, nargs='+', help='list of .md files to read')
args = parser.parse_args()

# create a list to hold the question-answer pairs
qa_pairs = []

# iterate over the list of files and extract the questions and answers
for filename in args.files:
    with open(filename, 'r') as file:
        lines = file.readlines()[1:] # ignore the first line
        question = None
        answer = None
        for line in lines:
            # check if the line contains a question
            question_match = question_regex.match(line)
            if question_match:
                # if there was a previous question and answer, add them to the list
                if question and answer:
                    answer = pypandoc.convert_text(answer, 'plain', format='md')
                    qa_pairs.append((question, answer))
                # store the new question
                question = question_match.group(1)
                answer = None
            else:
                # check if the line contains an answer
                answer_match = answer_regex.match(line)
                if answer_match:
                    # concatenate the answer to the previous answer
                    answer = (answer or '') + answer_match.group(1) + '\n'
        # add the last question and answer to the list, if there was one
        if question and answer:
            answer = pypandoc.convert_text(answer, 'plain', format='md')
            qa_pairs.append((question, answer))

# create a TTS object for each question-answer pair
tts_files = []
for question, answer in qa_pairs:
    text = f'{question}. {answer}'
    tts = gTTS(text=text, lang=language)
    tts_file = f'{question}.mp3'
    tts_file = re.sub('[^\w\-_\. ]', '_', f'{question}.mp3')

    try:
        tts.save(tts_file)
        tts_files.append(tts_file)
    except AttributeError:
        print(f"[WARNING] Skipping question '{question}' due to TTS error")

# concatenate the audio into a single MP3 file
output = AudioSegment.empty()
for tts_file in tts_files:
    try:
        audio = AudioSegment.from_file_using_temporary_files(tts_file)
        output += audio
    except Exception:
        print(f"[WARNING] Skipping file '{tts_file}' due to error")

output.export('output.mp3', format='mp3')

