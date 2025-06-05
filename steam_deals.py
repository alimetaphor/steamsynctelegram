import requests
from bs4 import BeautifulSoup

def fetch_discounted_games(limit=10):
    url = "https://store.steampowered.com/search/?specials=1"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    games = []
    result_rows = soup.find_all("a", class_="search_result_row")[:limit]

    for row in result_rows:
        title = row.find("span", class_="title").text.strip()
        link = row["href"].split("?")[0].strip()

        discount_block = row.find("div", class_="search_price_discount_combined")
        discount_text = discount_block.find("div", class_="search_discount").text.strip() if discount_block else ""

        price_block = discount_block.find("div", class_="search_price") if discount_block else None
        if price_block:
            price_parts = price_block.text.strip().split("zا")  # handles some localization
            final_price = price_parts[-1].strip()
            original_price = price_parts[0].strip() if len(price_parts) > 1 else final_price
        else:
            final_price = original_price = "نامشخص"

        games.append({
            "title": title,
            "link": link,
            "discount": discount_text,
            "original_price": original_price,
            "final_price": final_price
        })

    return games

# مثال کاربری:
if __name__ == "__main__":
    test_games = fetch_discounted_games(5)
    for i, g in enumerate(test_games, 1):
        print(f"{i}. {g['title']} - {g['discount']} | {g['final_price']}  (was {g['original_price']})\n{g['link']}\n")
