""" This script is used for writing in HTML files

It adds links to HTML table.
It generates span tags for un/colored matching blocks.
It compares two text files
It inserts comparison results in corresponding html files

"""
import os
from os import fsync, rename, path
from random import randint
from shutil import copy

from bs4 import BeautifulSoup as Bs
from tabulate import tabulate

from .html_utils import get_color_from_similarity, get_real_matching_blocks, \
    blocks_list_to_strings_list, get_ordered_blocks_positions
from .utils import is_float

from colour import Color
red = Color("#B1D9A3")
colors = list(red.range_to(Color("#FCBABA"),11))


def add_links_to_html_table(html_path: str) -> None:
    """ Add links to HTML data cells at specified path

    This method will link to all HTML TD tags which contain a float different from - 1 the
    corresponding HTML comparison file. The links will be opened in a new tab. The colors of
    the text in tag will change depending on similarity score.

    """

    with open(html_path, encoding='utf-8') as html:
        soup = Bs(html, 'html.parser')
        file_ind = 0  # Cursor on file number for the naming of html files
        print(html_path)
        for td_tag in soup.findAll('td'):  # Retrieve all data cells from html table in path
            if is_float(td_tag.text):  # If td is not filename or -1
                file_link = 'results\\' + html_path.split('\\')[-2] + '_' + str(file_ind),
                tmp = soup.new_tag('a',
                                   href=file_link,
                                   target="_blank",
                                    style = "color:black"
                                   )
                color = colors[int(float(td_tag.text)/10)]
                td_tag['style'] = f"background-color: {color};  padding: 20px;  border: 1px solid;"
                td_tag.string.wrap(tmp)  # We wrap the td string between the hyperlink
                file_ind += 1
            elif td_tag.text.strip() =="-1":
                td_tag['style'] = f"background-color: {colors[9]};  padding: 20px;  border: 1px solid;"
            else:
                if "entailment" in td_tag.text:
                    
                    td_tag['style'] = f"background-color: #FCBABA;  padding: 20px;  border: 1px solid;"
                    file_link = 'results\\' + html_path.split('\\')[-2] + '_' + str(file_ind),
                    tmp = soup.new_tag('a',
                                    href=file_link,
                                    target="_blank",
                                        style = "color:black"
                                    )
                    td_tag.string.wrap(tmp)  # We wrap the td string between the hyperlink
                    file_ind += 1
                elif "contradiction" in td_tag.text:
                    
                    td_tag['style'] = f"background-color: #B1D9A3;  padding: 20px;  border: 1px solid;"
                    file_link = 'results\\' + html_path.split('\\')[-2] + '_' + str(file_ind),
                    tmp = soup.new_tag('a',
                                    href=file_link,
                                    target="_blank",
                                        style = "color:black"
                                    )
                    td_tag.string.wrap(tmp)  # We wrap the td string between the hyperlink
                    file_ind += 1
                elif "neutral" in td_tag.text:
                    td_tag['style'] = f"background-color: #B1D9A3;  padding: 20px;  border: 1px solid;"
                    file_link = 'results\\' + html_path.split('\\')[-2] + '_' + str(file_ind),
                    tmp = soup.new_tag('a',
                                    href=file_link,
                                    target="_blank",
                                        style = "color:black"
                                    )
                    td_tag.string.wrap(tmp)  # We wrap the td string between the hyperlink
                    file_ind += 1
                else:
                    td_tag['style'] = f"background-color: #7cd1de;  padding: 20px;  border: 1px solid;"
                    
        for table_tag in soup.findAll('table'):
            table_tag['style'] = """ table-layout: fixed;  border: 1px solid;
  width: 70%;
  border-collapse: collapse;
  border: 3px solid purple;"""


        # We update the HTML of the file at path
        with open(html_path, 'wb') as f_output:
            f_output.write(soup.prettify("utf-8"))
            f_output.flush()
            fsync(f_output.fileno())
            f_output.close()


def get_span_blocks(bs_obj: Bs, text1: list, text2: list, block_size: int) -> list:
    """ Return list of spans with colors for HTML rendering """

    results = [[], []]  # List of spans list

    # Get matching blocks with chosen minimum size
    matching_blocks = get_real_matching_blocks(text1, text2, block_size)

    # Generate one unique color for each matching block
    colors = [f'#%06X' % randint(0, 0xFFFFFF) for _ in range(len(matching_blocks))]

    # Convert blocks from list of list of strings to list of strings
    string_blocks = [' '.join(map(str, text1[b.a:b.a + b.size])) for b in matching_blocks]

    # Store lengths of blocks in text
    strings_len_list = blocks_list_to_strings_list(matching_blocks, text1)

    # Convert list of strings to strings
    str1, str2 = ' '.join(map(str, text1)), ' '.join(map(str, text2))

    global_positions_list = [get_ordered_blocks_positions(str1, matching_blocks,
                                                          string_blocks),
                             get_ordered_blocks_positions(str2, matching_blocks,
                                                          string_blocks)]

    for num, pos_list in enumerate(global_positions_list):
        cursor = 0  # Cursor on current string

        if num == 1:  # Second iteration on second string
            str1 = str2

        for block in pos_list:
            # Span tag for the text before the matching sequence
            span = bs_obj.new_tag('span')
            span.string = str1[cursor:block[0]]

            # Span tag for the text in the matching sequence
            blockspan = bs_obj.new_tag('span',
                                       style="color:" + colors[block[1]] + "; font-weight:bold")
            blockspan.string = str1[block[0]:block[0] + strings_len_list[block[1]]]

            # Append spans tags to results list
            results[num].append(span)
            results[num].append(blockspan)

            # Update cursor position after last matching sequence
            cursor = block[0] + strings_len_list[block[1]]

        # End of loop, last span tag for the rest of the text
        span = bs_obj.new_tag('span')
        span.string = str1[cursor:]
        results[num].append(span)

    return results


def papers_comparison(save_dir: str, ind: int, text1: list, text2: list, filenames: tuple,
                      block_size: int) -> None:
    """ Write to HTML file texts that have been compared with highlighted similar blocks """

    copy(os.getcwd() + '/templates/template.html', save_dir)  # Copy comparison template to curr dir
    comp_path = path.join(save_dir, str(ind) + '.html')
    rename(path.join(save_dir, 'template.html'), comp_path)

    with open(comp_path, encoding='utf-8') as html:

        soup = Bs(html, 'html.parser')
        res = get_span_blocks(soup, text1, text2, block_size)
        blocks = soup.findAll(attrs={'class': 'block'})

        # Append filename tags and span tags to html
        for i, filename in enumerate(filenames):
            temp_tag = soup.new_tag('h3')
            temp_tag.string = filename
            blocks[i].append(temp_tag)
            for tag in res[i]:
                blocks[i].append(tag)

    with open(comp_path, 'wb') as f_output:
        f_output.write(soup.prettify("utf-8"))

#
# def results_to_html(scores: list, files_names: list, html_path: str) -> None:
#     """  Write similarity results to HTML page """
#     print(scores)
#     result = """   <!DOCTYPE html>
#                     <html>
#                       <head>
#                         <title>Result Page</title>
#                         <script src="https://cdn.anychart.com/releases/8.7.1/js/anychart-core.min.js"></script>
#                         <script src="https://cdn.anychart.com/releases/8.7.1/js/anychart-heatmap.min.js"></script>
#                         <style>
#                           html, body {
#                             width: 100%;
#                             height: 100%;
#                             margin: 0;
#                             padding: 0;
#                           }
#                           #container{
#                           height:50%;
#                           }
#                         </style>
#                       </head>
#                       <body> <div id="container"></div>
#                         <script>
#                           anychart.onDocumentReady(function () {
#                           var data = [\n"""
#     for i, file1 in enumerate(files_names):
#         for j, file2 in enumerate(files_names):
#             if i != j:
#                 score = scores[i][j] / 100
#                 print(score)
#                 result += '{x:"%s",y:"%s",heat:%f},\n' % (file1, file2, score)
#                 continue
#             result += '{x:"%s",y:"%s",heat:%d},\n' % (file1, file2, 0)
#     result += """
#                                         ];
#
#                                             chart = anychart.heatMap(data);
#
#                                             chart.title("Result Heatmap");
#
#                                             var customColorScale = anychart.scales.linearColor();
#                                             customColorScale.colors(["#ACE8D4", "#00726A"]);
#
#                                             chart.colorScale(customColorScale);
#
#                                             chart.container("container");
#
#                                             chart.draw();
#
#                                           });
#                                         </script>
#                                         </body>
#                                     </html>
#     """
#     with open(html_path, 'w', encoding='utf-8') as file:
#         file.write(result)
#         file.flush()
#         fsync(file.fileno())
#         file.close()


def results_to_html(scores: list, files_names: list, html_path: str) -> None:
    """  Write similarity results to HTML page """

    for ind, _ in enumerate(files_names):
        scores[ind].insert(0, files_names[ind])

    scores.insert(0, files_names)
    scores[0].insert(0, 'Result HeatMap')

    with open(html_path, 'w', encoding='utf-8') as file:
       
        file.write('{% extends "plagiarism/base.html" %}\n{% block content %}'+tabulate(scores, tablefmt='html')+'\n{% endblock %}')
        file.flush()
        fsync(file.fileno())
        file.close()