from pathlib import Path
import shutil
import re
import csv

import requests
from bs4 import BeautifulSoup
from terminaltables import AsciiTable
from tqdm import tqdm

import main

CURRENT_DIR = Path.cwd()
DATA_DIR = CURRENT_DIR / "data"
IMAGES_DIR_NAME = "images"


def connect_status(link):

    print("\nChecking connection...")

    r = requests.get(link)

    if r.status_code in [200, 201]:
        return True

    print(f"\nConnection to {link} is not impossible"
          "Exiting script\n")
    exit()


def all_categories(link):

    # Home connection
    r_home = requests.get(link)

    # Home page soup
    soup_home = BeautifulSoup(r_home.content, 'html.parser')

    # Categories list
    cat_list = []
    souped_links = soup_home.select(".side_categories ul li ul li a")
    for a in souped_links:
        cat_name = a.get_text(strip=True)
        cat_link = f"{main.HOME}/{a['href'].replace('/index.html', '')}"
        cat_list.append({'name': cat_name, 'link': cat_link})

    # Alphabetical order of list's categories
    cat_list.sort(key=lambda x: x['name'])

    return cat_list


def cat_selection(cat_list: list):

    # Header
    print(f"\nListe des catégories trouvées")

    # Categories table
    cat_table = [['ID', 'Category', 'link']]
    cat_table.extend([f"[{cat_list.index(i) + 1}]", i['name'], i['link']] for i in cat_list)
    print(AsciiTable(cat_table).table)

    # User choice
    while True:
        user = input("Enter the category [index] to download it or [All] for all categories at once: ").lower()
        if user == 'all':
            return cat_list
        elif int(user) in range(1, len(cat_list) + 1):
            return [cat_list[int(user) - 1]]
        else:
            print("Invalid input.")


def dir_manager(cat_list: list):
    """
    Target directories for files and downloads
    :param cat_list: Categories list which will be extracted form the website
    :return:
    """

    if not DATA_DIR.exists():
        DATA_DIR.mkdir()

    file_paths = {}

    for cat in cat_list:

        # Categories directories
        cat_path = DATA_DIR / cat['name']
        if cat_path.exists():
            shutil.rmtree(cat_path)
        cat_path.mkdir()
        cat_path_images = cat_path / IMAGES_DIR_NAME
        cat_path_images.mkdir()

        # Output data file
        data_file = cat_path / f"{cat['name']}.csv"
        data_file.touch()
        file_paths[cat['name']] = data_file

    return file_paths


def scraper(cat_list: list, files_paths: dict):

    for cat in cat_list:

        cat_books = []

        # Category scraping
        books = category_scraper(cat['link'])

        # Header of each downloading bar
        print(f"\n{cat_list.index(cat) + 1 }/{len(cat_list)} - Category '{cat['name']}': {books[0]} book(s) found.")

        # ----- Extracting books data ----- #
        dir_cat = DATA_DIR / cat['name']
        for book_link in tqdm(books[1], ncols=100, desc="Extracting "):
            book_infos = book_scraper(cat['name'], book_link, dir_cat)
            cat_books.append(book_infos)

        # ----- Formatting data ----- #
        f_data = format_data(cat_books)

        # ----- Loading data to CSV file ----- #
        file_writer(f_data, files_paths[cat['name']])

        print(f"Scrape of '{cat['name']}': success\n")


def category_scraper(cat_home):

    # Connexion and souping cat_url
    r_cat_home = requests.get(cat_home)
    soup_cat_home = BeautifulSoup(r_cat_home.content, 'html.parser')

    # Books number
    nb_books = int(soup_cat_home.find(class_="form-horizontal").find("strong").get_text(strip=True))

    # Category's list of books urls from category's index page
    books_links = [link.get('href') for link in soup_cat_home.select(".product_pod h3 a")]

    # Category's list of books urls from category's next pages if existed
    i = 2
    while True:
        r_cat_next = requests.get(f"{cat_home}/page-{i}.html")
        if r_cat_next.status_code not in [200, 201]:
            break
        soup_cat_url_next = BeautifulSoup(r_cat_next.content, 'html.parser')
        books_links_next = [link.get('href') for link in soup_cat_url_next.select(".product_pod h3 a")]
        books_links.extend(iter(books_links_next))
        i += 1

    # Relative to absolute links
    books_links = [link.replace('../../..', f"{main.HOME}/catalogue") for link in books_links]

    return nb_books, books_links


def book_scraper(cat, link, cat_dir):

    # Connexion and souping book page
    r_book = requests.get(link)
    soup_book = BeautifulSoup(r_book.content, 'html.parser').find(class_="product_page")

    # Book infos
    title = soup_book.find(class_="product_main").find("h1").get_text(strip=True)
    soup_table = soup_book.find("table")
    upc = soup_table.select("td")[0].get_text(strip=True)
    price_it = soup_table.select("td")[2].get_text(strip=True)
    price_et = soup_table.select("td")[3].get_text(strip=True)
    stock = soup_table.select("td")[5].get_text(strip=True)
    stars = soup_book.find(class_="star-rating").attrs.get('class')[1]
    # Description not present in all book pages
    try:
        try_descr = soup_book.select("#product_description + p")[0].get_text(strip=True)
    except IndexError:
        p_descr = ""
    else:
        p_descr = try_descr

    # Image Download
    image_url = soup_book.find('img')['src'].replace("../..", main.HOME)
    r_image = requests.get(image_url, stream=True)
    image_name = soup_book.find('img')['alt'].replace(" ", "_").replace("/", "-") + ".jpg"
    img_path = cat_dir / IMAGES_DIR_NAME / image_name
    with open(img_path, mode='wb') as f:
        shutil.copyfileobj(r_image.raw, f)

    return {"link": link,
            "upc": upc,
            "title": title,
            "price_it": price_it,
            "price_et": price_et,
            "stock": stock,
            "p_descr": p_descr,
            "cat": cat,
            "stars": stars,
            "img_url": image_url}


def format_data(book_list: list):

    # Dictionary used to transform rating from letters to numbers
    rating_dict = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

    # Formatting data
    for book in tqdm(book_list, ncols=100, desc="Formatting "):
        setup_format(book, rating_dict)

    return book_list


def setup_format(book, rating_dict):
    book["title"] = book["title"].title()
    book["price_it"] = float(book["price_it"].lstrip("£"))
    book["price_et"] = float(book["price_et"].lstrip("£"))
    book["stock"] = re.sub(r"\D", "", book["stock"])
    book["cat"] = book["cat"].capitalize()
    book["stars"] = rating_dict[book["stars"]]
    book["img_url"] = book["img_url"].replace("../..", main.HOME)


def file_writer(data: list, file_path):

    fields_name = ["product_page_url",
                   "universal_product_code",
                   "title",
                   "price_including_tax",
                   "price_excluding_tax",
                   "number_available",
                   "product_description",
                   "category",
                   "review_rating",
                   "image_url"]

    # Writing CSV fields names
    with open(file_path, mode='w') as f:
        csvwriter = csv.writer(f)
        csvwriter.writerow(fields_name)

    for book in tqdm(data, ncols=100, desc='Loading    '):
        data_to_csv = [book["link"],
                       book["upc"],
                       book["title"],
                       book["price_it"],
                       book["price_et"],
                       book["stock"],
                       book["p_descr"],
                       book["cat"],
                       book["stars"],
                       book["img_url"]]

        # Writing book infos in data file
        with open(file_path, mode='a') as f:
            csvwriter = csv.writer(f)
            csvwriter.writerow(data_to_csv)


def one_more():
    while True:
        another = input("Do you want to download another category? [y] or [N]: ").lower()
        if another == "y":
            return True
        elif another == "n":
            exit()
        else:
            print("Invalid input.")
