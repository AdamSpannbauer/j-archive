import numpy as np
import pandas as pd
from bs4 import BeautifulSoup

HTML_PARSER = 'html.parser'
ROBOTS_TXT_URL = 'http://www.j-archive.com/robots.txt'
EPISODE_BASE_URL = 'http://www.j-archive.com/showgame.php?game_id='


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


def parse_fj(page_soup):
    fj_board = page_soup.select_one('.final_round')
    category = fj_board.select_one('.category_name').text

    response_html = fj_board.find('div', {'onmouseover': True})['onmouseover']
    response_soup = BeautifulSoup(response_html, HTML_PARSER)
    correct_responders = response_soup.select('.right')
    correct_responders = [cr.text for cr in correct_responders]

    correct_response = response_soup.select('em')[-1].text

    rows = []
    row = []
    response_table = response_soup.select('tr')
    for row_i, tr in enumerate(response_table):
        td = tr.find_all('td')
        contents = [tr.text for tr in td]
        if row_i % 2 == 0:
            row = contents
        else:
            row += contents
            rows.append(row)

    df = pd.DataFrame(rows, columns=['responder', 'response', 'wager'])
    df['is_correct'] = df['responder'].isin(correct_responders)
    df['category'] = category
    df['correct_response'] = correct_response

    return df


def parse_score_tables(soup):
    first_ad_break_scores = str(soup.select_one('#jeopardy_round > table:nth-child(4)'))
    jeopardy_scores = str(soup.select_one('#jeopardy_round > table:nth-child(6)'))
    d_jeopardy_scores = str(soup.select_one('#double_jeopardy_round > table:nth-child(4)'))
    f_jeopardy_scores = str(soup.select_one('#final_jeopardy_round > table:nth-child(4)'))

    score_strs = [first_ad_break_scores, jeopardy_scores, d_jeopardy_scores, f_jeopardy_scores]
    score_dfs = []
    for ss in score_strs:
        df = pd.read_html(ss)[0]
        df = df.T

        names = ['player', 'value']
        if df.shape[1] > 2:
            names += ['additional_info']

        df.columns = names
        score_dfs.append(df)

    scores_df = pd.concat(score_dfs, sort=False)

    return scores_df


def scrape_episode(scraper, episode_num):
    episode_url = EPISODE_BASE_URL + str(episode_num)
    page_html = scraper.get_page(episode_url)

    soup = BeautifulSoup(page_html, features=HTML_PARSER)
    episode_df = parse_rounds(soup)
    episode_df['episode'] = episode_num

    final_jep_df = parse_fj(soup)

    scores_df = parse_score_tables(soup)

    return episode_df, final_jep_df, scores_df


if __name__ == '__main__':
    import os
    from scraper import Scraper

    CSV_OUTPUT_DIR = 'data'

    j_scraper = Scraper(robots_txt_url=ROBOTS_TXT_URL)
    for i in range(1, 21):
        print(f'Scraping/parsing episode #{i}')
        ep_df, fj_df, score_df = scrape_episode(j_scraper, episode_num=i)

        episode_csv = os.path.join(CSV_OUTPUT_DIR, 'episode', f'show_{i}.csv')
        fj_csv = os.path.join(CSV_OUTPUT_DIR, 'final_jep', f'show_{i}.csv')
        score_csv = os.path.join(CSV_OUTPUT_DIR, 'score', f'show_{i}.csv')

        ep_df.to_csv(episode_csv, index=False)
        fj_df.to_csv(fj_csv, index=False)
        score_df.to_csv(score_csv, index=False)
