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
