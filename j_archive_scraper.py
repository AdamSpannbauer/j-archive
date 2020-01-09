# TODO: parse final jeopardy info

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from scraper import Scraper

ROBOTS_TXT_URL = 'http://www.j-archive.com/robots.txt'
HTML_PARSER = 'html.parser'


def category_name(board_html):
    category_names_html = board_html.select('.category_name')
    cats = []
    for category_name_html in category_names_html:
        cat = category_name_html.text
        cats.append(cat)

    return cats


def parse_response(clue_html):
    correct_response_html = clue_html.find('div', {'onmouseover': True})['onmouseover']
    correct_response_soup = BeautifulSoup(correct_response_html, HTML_PARSER)
    correct_response = correct_response_soup.select_one('.correct_response')
    correct_response = correct_response.text

    correct_responder = correct_response_soup.select_one('.right')
    incorrect_responder = correct_response_soup.select_one('.wrong')

    if correct_responder:
        responder = correct_responder.text
        is_correct = True
    else:
        responder = incorrect_responder.text
        is_correct = False

    return {'correct_response': correct_response,
            'responder': responder,
            'is_correct': is_correct}


def parse_value(clue_html):
    value = clue_html.select_one('.clue_value')
    dd_value = clue_html.select_one('.clue_value_daily_double')

    if dd_value:
        value = dd_value.text.replace('DD: ', '')
        is_dd = True
    else:
        value = value.text
        is_dd = False

    value = value.replace('$', '')

    return {'value': value,
            'is_daily_double': is_dd}


def parse_clues(board_html):
    clues_html = board_html.select('.clue')

    clue_dicts = []
    for clue_html in clues_html:
        if clue_html.text.strip():
            value_dict = parse_value(clue_html)
            response_dict = parse_response(clue_html)

            answer = clue_html.select_one('.clue_text').text
            order_number = clue_html.select_one('.clue_order_number').text

            clue_dict = {'answer': answer,
                         'order_number': order_number}
            clue_dict.update(value_dict)
            clue_dict.update(response_dict)
        else:
            keys = ['answer', 'order_number', 'value', 'is_daily_double',
                    'correct_response', 'responder', 'is_correct']
            clue_dict = {k: np.nan for k in keys}

        clue_dicts.append(clue_dict)

    return pd.DataFrame(clue_dicts)


def parse_rounds(page_soup):
    boards = page_soup.select('.round')

    clue_dfs = []
    for round_num, board in enumerate(boards):
        categories = category_name(board)
        clue_df = parse_clues(board)
        clue_df['category'] = categories * 5
        clue_df['round_num'] = round_num + 1
        clue_dfs.append(clue_df)

    return pd.concat(clue_dfs)


# TODO: parse final jeopardy info
def parse_fj_clue(fj_clue_html):
    # fj_clue = board.find('td', {'id': 'clue_FJ'})
    pass


if __name__ == '__main__':
    PAGE_URL = 'http://www.j-archive.com/showgame.php?game_id='
    CSV_OUTPUT = 'example_data.csv'

    episode_num = 4000
    TEST_HTML_OUTPUT = 'example_page.html'
    TEST_PAGE_URL = PAGE_URL + str(episode_num)

    # Test page scrape.
    # There's a 20 sec crawl delay so... just use the test page until real scrape time
    # scraper = Scraper(robots_txt_url=ROBOTS_TXT_URL)
    # page_html = scraper.get_page(TEST_PAGE_URL)
    #
    # with open(TEST_HTML_OUTPUT, 'w') as f:
    #     f.write(page_html)

    with open(TEST_HTML_OUTPUT, 'r') as f:
        page_html = f.read()

    soup = BeautifulSoup(page_html, features=HTML_PARSER)
    episode_df = parse_rounds(soup)
    episode_df['episode'] = episode_num
    episode_df.to_csv(CSV_OUTPUT, index=False)
