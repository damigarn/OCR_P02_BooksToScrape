import requests

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