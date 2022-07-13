from django.shortcuts import render
from django.http import HttpResponse
import os

import sys
import webbrowser
from datetime import datetime
from os import listdir, path
import os

from  plagiarism.scripts.html_writing import add_links_to_html_table, results_to_html, papers_comparison
from  plagiarism.scripts.html_utils import writing_results
from  plagiarism.scripts.processing_files import file_extension_call
from  plagiarism.scripts.similarity import difflib_overlap,calculate_jaccard,calculate_overlap
from  plagiarism.scripts.utils import wait_for_file, get_student_names, parse_options

import tensorflow as tf
import transformers
import numpy as np

new_model = tf.saved_model.load('C:\\Users\\bhatd\\Downloads\\bert_siamese_v1-20220627T125410Z-001\\bert_siamese_v1')

max_length = 128  # Maximum length of input sentence to the model.
batch_size = 32
epochs = 2

# Labels in our dataset.
labels = ["contradiction", "entailment", "neutral"]

# Create your views here.

def home(request):
    if request.user.is_authenticated:
        context = {"username": request.user.username}
        return render(request,'plagiarism/home.html', context=context)
    return render(request, "plagiarism/home.html", context={"username":request.user.username})


def render_result(request, file_path):
    file_name = file_path.split('_')[-1]
    folder_name = "_".join(file_path.split('_')[:2])
    return render(request, 'results/' + folder_name + "/" + file_name + '.html')


def checker(request):
    if request.method == "POST":

        in_dir = request.POST["input_dir"]
        method = request.POST["method"]
        print(in_dir)
        result_dir = check_plagiarism_from_indirectory(in_dir,method)
        return render(request, result_dir)
    print(os.getcwd())
    return render(request, "plagiarism/check.html", context={"username":request.user.username})


def contact(request):
    if request.user.is_authenticated:
        context = {"username": request.user.username}
        return render(request,'plagiarism/contact.html', context=context)
    return render(request, "plagiarism/contact.html", context={"username":request.user.username})


def about(request):
    if request.user.is_authenticated:
        context = {"username": request.user.username}
        return render(request,'plagiarism/about.html', context=context)
    return render(request, "plagiarism/about.html", context={"username":request.user.username})



class BertSemanticDataGenerator(tf.keras.utils.Sequence):
    """Generates batches of data.

    Args:
        sentence_pairs: Array of premise and hypothesis input sentences.
        labels: Array of labels.
        batch_size: Integer batch size.
        shuffle: boolean, whether to shuffle the data.
        include_targets: boolean, whether to incude the labels.

    Returns:
        Tuples `([input_ids, attention_mask, `token_type_ids], labels)`
        (or just `[input_ids, attention_mask, `token_type_ids]`
         if `include_targets=False`)
    """

    def __init__(
        self,
        sentence_pairs,
        labels,
        batch_size=batch_size,
        shuffle=True,
        include_targets=True,
    ):
        self.sentence_pairs = sentence_pairs
        self.labels = labels
        self.shuffle = shuffle
        self.batch_size = batch_size
        self.include_targets = include_targets
        # Load our BERT Tokenizer to encode the text.
        # We will use base-base-uncased pretrained model.
        self.tokenizer = transformers.BertTokenizer.from_pretrained(
            "bert-base-uncased", do_lower_case=True
        )
        self.indexes = np.arange(len(self.sentence_pairs))
        self.on_epoch_end()

    def __len__(self):
        # Denotes the number of batches per epoch.
        return len(self.sentence_pairs) // self.batch_size

    def __getitem__(self, idx):
        # Retrieves the batch of index.
        indexes = self.indexes[idx * self.batch_size : (idx + 1) * self.batch_size]
        sentence_pairs = self.sentence_pairs[indexes]

        # With BERT tokenizer's batch_encode_plus batch of both the sentences are
        # encoded together and separated by [SEP] token.
        encoded = self.tokenizer.batch_encode_plus(
            sentence_pairs.tolist(),
            add_special_tokens=True,
            max_length=max_length,
            return_attention_mask=True,
            return_token_type_ids=True,
            pad_to_max_length=True,
            return_tensors="tf",
        )

        # Convert batch of encoded features to numpy array.
        input_ids = np.array(encoded["input_ids"], dtype="int32")
        attention_masks = np.array(encoded["attention_mask"], dtype="int32")
        token_type_ids = np.array(encoded["token_type_ids"], dtype="int32")

        # Set to true if data generator is used for training/validation.
        if self.include_targets:
            labels = np.array(self.labels[indexes], dtype="int32")
            return [input_ids, attention_masks, token_type_ids], labels
        else:
            return [input_ids, attention_masks, token_type_ids]

    def on_epoch_end(self):
        # Shuffle indexes after each epoch if shuffle is set to True.
        if self.shuffle:
            np.random.RandomState(42).shuffle(self.indexes)


def check_semantic_bert(sentence1, sentence2):
    sentence1 = " ".join(sentence1)
    sentence2 = " ".join(sentence2)
    sentence_pairs = np.array([[str(sentence1), str(sentence2)]])
    test_data = BertSemanticDataGenerator(
        sentence_pairs, labels=None, batch_size=1, shuffle=False, include_targets=False)
    proba = new_model(test_data[0])[0]
    idx = np.argmax(proba)
    proba = f"{proba[idx]: .2f}%"
    pred = labels[idx]
    return pred, proba


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
                print(file_words[:10])
                if file_words:  # If all files have supported format
                    processed_files.append(file_words)
                    filenames.append(students_names[ind])
                else:  # At least one file was not supported
                    print(
                        "Remove files which are not txt, pdf, docx or odt and run the "
                        "script again.")
                    sys.exit()
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
                            if i>j:
                                difflib_scores[i].append(check_semantic_bert(text_bis, text))
                            else:
                                difflib_scores[i].append(check_semantic_bert(text, text_bis))
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

