#!/usr/bin/env python
""" This module launches the files comparison process

This modules compares all txt, docs, odt, pdf files present in path specified as argument.
It writes results in a HTML table.
It uses difflib library to find matching sequences.
It can also use Jaccard Similarity, words counting, overlapping words for similarity

"""
import logging

logger = logging.getLogger(__name__)

import sys
import webbrowser
from datetime import datetime
from os import listdir, path
import os

from .html_writing import add_links_to_html_table, results_to_html, papers_comparison
from .html_utils import writing_results
from .processing_files import file_extension_call
from .similarity import difflib_overlap,calculate_jaccard,bert_similarity
from .utils import wait_for_file, get_student_names, parse_options

# def get_web_data():
#     import requests 
#     from bs4 import BeautifulSoup
#     links=[""]
#     for i in 
#     link = 'https://www.javatpoint.com/osi-model'
#     data = requests.get(link)

#     soup = BeautifulSoup(data.text,'lxml')
#     article  = soup.find('div',class_= 'onlycontent').find('div',class_ = 'onlycontentinner').find('div',{'id':'city'}).text
# print(article)
def check_plagiarism_from_indirectory(in_dir,method):
    # out_dir = os.getcwd() + 'plagiarism/results'
    out_dir = None
    block_size = None
    
    print(out_dir)
    if path.exists(in_dir):  # Check if specified path exists

        if len(listdir(in_dir)) > 1:  # Check if there are at least 2 files at specified path
            filenames, processed_files = [], []
            students_names = get_student_names(in_dir)
            print(students_names)
            for ind, file in enumerate(listdir(in_dir)):

                file_words = file_extension_call(in_dir + '/' + file)
                logger.warning(file_words)
                
                if file_words:  # If all files have supported format
                    processed_files.append(file_words)
                    filenames.append(students_names[ind])
                else:  # At least one file was not supported
                    print(
                        "Remove files which are not txt, pdf, docx or odt and run the "
                        "script again.")
            if out_dir is not None and path.exists(out_dir):
                results_directory = out_dir
            else:
                # Create new directory for storing html files
                results_directory = writing_results(datetime.now().strftime("%Y%m%d_%H%M%S"))

            difflib_scores = [[] for _ in range(len(processed_files))]
            file_ind = 0
            for i, text in enumerate(processed_files):
                for j, text_bis in enumerate(processed_files):
                    if i != j:
                        # Append to the list the similarity score between text and text_bis
                        if method == "bert":
                            difflib_scores[i].append(check_semantic_bert(text_bis, text))
                        elif method == "sequence_matcher":
                            difflib_scores[i].append(difflib_overlap(text, text_bis))
                        elif method == "jaccard_algorithm":
                            difflib_scores[i].append(calculate_jaccard(text, text_bis))
                        elif method == "overlap":
                            difflib_scores[i].append(calculate_overlap(text, text_bis))

                        # Write text with matching blocks colored in results directory
                        papers_comparison(results_directory, file_ind, text, text_bis,
                                          (filenames[i], filenames[j]), block_size)
                        file_ind += 1
                    else:
                        difflib_scores[i].append(-1)
            results_directory = path.join(results_directory, '_results.html')
       
            print(difflib_scores)
            results_to_html(difflib_scores, filenames, results_directory)

            if wait_for_file(results_directory, 60):  # Wait for file to be created
                add_links_to_html_table(results_directory) # Open results HTML table
            else:
                print("Results file was not created...")
        else:
            print(
                "Minimum number of files is not present. Please check that there are at least "
                "two files to compare.")
            sys.exit()
    else:
        print("The specified path does not exist : " + in_dir)
        sys.exit()
    return results_directory

