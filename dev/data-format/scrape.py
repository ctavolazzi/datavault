from main import DataFetcher

def main():
    # Initialize the fetcher with our config
    fetcher = DataFetcher("d.json")

    # Attempt to fetch the data
    print("Starting scrape...")
    success = fetcher.fetch_source("scrape_this_site")

    if success:
        print("Successfully scraped and saved the webpage!")
        print(f"Data saved to: {fetcher.config['sources'][0]['storage_path']}")
    else:
        print("Failed to scrape the webpage.")

if __name__ == "__main__":
    main()