from pathlib import Path
import shutil

import requests
from bs4 import BeautifulSoup

HOME_URL = "https://books.toscrape.com"


# Home connection
r_home = requests.get(HOME_URL)

# Welcome message
if r_home.status_code in [200, 201]:
    print(f"\nConnection to {HOME_URL} is OK\n")
    print()
else:
    print(f"\nConnection to {HOME_URL} is not impossible\n"
          "Exiting script\n")

# Home page soup
soup_home = BeautifulSoup(r_home.content, 'html.parser')

# Dictionnaire → Clé : Nom de la catégorie ; Valeur : lien index.html de la catégorie
dict_categories = {}
for a in soup_home.select(".side_categories ul li ul li a"):
    dict_categories[a.get_text(strip=True)] = f"{HOME_URL}/{a['href'].replace('/index.html', '')}"

# Print the number of categories
nbCategories = len(dict_categories)
print(f"{nbCategories} catégories trouvées.")

# Target directory for database
cat_data = Path.cwd() / "Data"
if cat_data.exists():
    shutil.rmtree(cat_data)
cat_data.mkdir()

# Categories pages exploration
# Dictionary needed for rating formatting. Here to avoid to be in the loop and to create an instance each time
dict_rating = {'One': '1/5', 'Two': '2/5', 'Three': '3/5', 'Four': '4/5', 'Five': '5/5'}
for cat, cat_url in dict_categories.items():

    # Progression category indicator
    indice_category = list(dict_categories.keys()).index(cat) + 1
    print(f"\n{indice_category}/{nbCategories} - Category '{cat}'")

    # Connexion and souping cat_url
    r_cat_url_one = requests.get(cat_url)
    soup_cat_url_one = BeautifulSoup(r_cat_url_one.content, 'html.parser')

    # Books number indicator
    nb_livres = int(soup_cat_url_one.find(class_="form-horizontal").find("strong").get_text(strip=True))
    print(f"Book(s) found : {nb_livres}")

    # Category's list of books urls from category's index page
    books_links = [link.get('href') for link in soup_cat_url_one.select(".product_pod h3 a")]

    # Category's list of books urls from category's next pages if existed
    i = 2
    while True:
        r_cat_url_next = requests.get(f"{cat_url}/page-{i}.html")
        if r_cat_url_next.status_code not in [200, 201]:
            break
        soup_cat_url_next = BeautifulSoup(r_cat_url_next.content, 'html.parser')
        books_links_next = [link.get('href') for link in soup_cat_url_next.select(".product_pod h3 a")]
        books_links.extend(iter(books_links_next))
        i += 1

    # Relative to absolute links
    books_links = [link.replace('../../..', f"{HOME_URL}/catalogue") for link in books_links]
