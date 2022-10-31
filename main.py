from pathlib import Path
import shutil
import csv

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

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

    # Category directories for downloading data
    cat_path = Path.cwd() / "Data" / cat
    cat_path_images = cat_path / "Images"
    cat_path.mkdir()
    cat_path_images.mkdir()

    # Category CSV data file
    data_file = cat_path / f"{cat}.csv"
    data_file.touch()
    fields = ["link",
              "universal_product_code",
              "title",
              "price_including_tax",
              "price_excluding_tax",
              "number_available",
              "product_description",
              "category",
              "review_rating",
              "image_url"]
    with open(data_file, mode='w') as f:
        csvwriter = csv.writer(f)
        csvwriter.writerow(fields)

    # Downloading data
    for link in tqdm(books_links, ncols=100, desc="Téléchargement"):
        # Scanning book infos
        r_book_page = requests.get(link)
        book_infos = BeautifulSoup(r_book_page.content, 'html.parser').find(class_="product_page")

        # Book infos
        universal_product_code = book_infos.find("table").select("td")[0].get_text(strip=True)
        title = book_infos.find(class_="product_main").find("h1").get_text(strip=True)
        price_including_tax = book_infos.find("table").select("td")[2].get_text(strip=True)
        price_excluding_tax = book_infos.find("table").select("td")[3].get_text(strip=True)
        number_available = book_infos.find("table").select("td")[5].get_text(strip=True)
        review_rating = book_infos.find(class_="star-rating").attrs.get('class')[1]
        image_url = book_infos.find('img')['src'].replace("../..", HOME_URL)
        image_name = book_infos.find('img')['alt'].replace(" ", "_").replace("/", "-") + ".jpg"
        # Description not all the time
        try:
            try_descr = book_infos.select("#product_description + p")[0].get_text(strip=True)
        except IndexError:
            product_description = ""
        else:
            product_description = try_descr

        # Image Download
        r_image = requests.get(image_url, stream=True)
        img_path = cat_path_images / image_name
        with open(img_path, mode='wb') as f:
            shutil.copyfileobj(r_image.raw, f)

        # Formatting books infos
        book_format = [link,
                       universal_product_code,
                       title.title(),
                       float(price_including_tax.lstrip("£")),
                       float(price_excluding_tax.lstrip("£")),
                       int(number_available.strip(" Instock(available)")),
                       product_description,
                       cat.capitalize(),
                       dict_rating[review_rating],
                       image_url.replace("../..", HOME_URL)]