import requests
from bs4 import BeautifulSoup

for tf in ['daily', 'weekly', 'monthly']:
    print(f"\n--- {tf.upper()} ---")
    url = f"https://github.com/trending?since={tf}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    for article in soup.find_all('article', class_='Box-row')[:3]:
        h2 = article.find('h2', class_='h3')
        if h2:
            repo_name = h2.text.strip().replace(' ', '').replace('\n', '')
            stars_span = article.find('span', class_='d-inline-block float-sm-right')
            if stars_span:
                stars_text = stars_span.text.strip()
                print(f"{repo_name}: {stars_text}")
