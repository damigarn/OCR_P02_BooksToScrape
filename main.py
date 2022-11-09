import scraper


# Website to scrape (Script only works with this url so HOME is a constant)
HOME = "https://books.toscrape.com"


def main():

    # Get all categories list and associated links
    cat_list = scraper.all_categories(HOME)

    # Category selection
    cat_select = scraper.cat_selection(cat_list)

    # Creation of directories and files to store data
    files_paths = scraper.dir_manager(cat_select)

    # Scraping
    scraper.scraper(cat_select, files_paths)

    # Another extraction ?
    if scraper.one_more():
        main()


if __name__ == "__main__" and scraper.connect_status(HOME):
    print(f"\nConnection to {HOME} is OK")
    main()
