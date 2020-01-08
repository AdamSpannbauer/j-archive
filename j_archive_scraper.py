from scraper import Scraper

ROBOTS_TXT_URL = 'http://www.j-archive.com/robots.txt'
TEST_PAGE_URL = 'http://www.j-archive.com/showgame.php?game_id=2'
OUTPUT = 'example_page.html'

scraper = Scraper(robots_txt_url=ROBOTS_TXT_URL)
page_html = scraper.get_page(TEST_PAGE_URL)

with open(OUTPUT, 'w') as f:
    f.write(page_html)
