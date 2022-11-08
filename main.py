import scraper


# Website to scrape (Script only works with this url so HOME is a constant)
HOME = "https://books.toscrape.com"


def main():

    # Liste de toutes les catégories et leurs liens associés
    cat_list = scraper.all_categories(HOME)

    # Category selection
    cat_select = scraper.cat_selection(cat_list)

    # Creation of directories and files to store data
    data_files = scraper.dir_manager(cat_select)

    # Extracting data
    data = scraper.scraper(cat_select)

    # Formatting data
    f_data = scraper.format_data(data)

    # Loading data
    scraper.file_writer(f_data, data_files)

    # Another extraction ?
    if scraper.one_more():
        main()


if __name__ == "__main__" and scraper.connect_status(HOME):
    print(f"\nConnection to {HOME} is OK")
    main()
