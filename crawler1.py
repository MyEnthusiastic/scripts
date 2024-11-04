import requests
from bs4 import BeautifulSoup
import json
import os

def get_dataset_urls():
    """Fetch all dataset documentation URLs from the main datasets page."""
    base_url = "https://pytorch.org/vision/stable/datasets.html"
    response = requests.get(base_url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch datasets page: {response.status_code}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all dataset links in the documentation
    dataset_urls = []
    # Look for links in the main content area that point to dataset documentation
    for link in soup.find_all('a', href=True):
        href = link['href']
        if 'generated/torchvision.datasets.' in href and 'html' in href:
            # Convert relative URLs to absolute URLs
            if href.startswith('http'):
                dataset_urls.append(href)
            else:
                full_url = f"https://pytorch.org/vision/stable/{href}"
                dataset_urls.append(full_url)
    
    return dataset_urls

def crawl_dataset_docs(url):
    """Crawl documentation for a single dataset."""
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch page: {response.status_code}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract dataset name from URL
    dataset_name = url.split('.')[-1]

    # Print URL and dataset name
    print(f"Processing URL: {url}")
    print(f"Dataset name: {dataset_name}")
    
    # Initialize dictionary to store the data
    dataset_info = {
        "Dataset Name": dataset_name,
        "Pytorch Dataset Website": url,
        "Dataset Description": soup.find('p').text.strip() if soup.find('p') else "",
        # TODO: change this to the one inside Pytorch Dataloader
        "full_class_name": f"torchvision.datasets.{dataset_name}",
        "parameters": [],
        "warnings": [],
        "returns": {}
    }
    
    # Get warnings
    warnings = soup.find_all('div', class_='warning')
    for warning in warnings:
        dataset_info["warnings"].append(warning.text.strip())
    
    # Get parameters
    param_list = soup.find('dl', class_='field-list')
    if param_list:
        params = param_list.find_all(['dt', 'dd'])
        current_param = None
        
        for item in params:
            if item.name == 'dt':
                current_param = item.text.strip()
            elif item.name == 'dd' and current_param:
                param_info = {
                    "name": current_param,
                    "description": item.text.strip()
                }
                dataset_info["parameters"].append(param_info)
    
    # Get return information
    returns_section = soup.find('dl', class_='py method')
    if returns_section:
        returns_items = returns_section.find_all(['dt', 'dd'])
        for i in range(0, len(returns_items), 2):
            if i + 1 < len(returns_items):
                key = returns_items[i].text.strip()
                value = returns_items[i + 1].text.strip()
                dataset_info["returns"][key] = value
    
    return dataset_info

def crawl_all_datasets():
    """Crawl documentation for all datasets and save them individually."""
    # Create a directory for the JSON files if it doesn't exist
    os.makedirs('dataset_docs', exist_ok=True)
    
    # Get all dataset URLs
    dataset_urls = get_dataset_urls()
    
    # Dictionary to store all dataset information
    all_datasets = {}

    # Clean the dataset_docs directory before starting
    for file in os.listdir('dataset_docs'):
        file_path = os.path.join('dataset_docs', file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting {file_path}: {str(e)}")
    
    # Crawl each dataset
    for url in dataset_urls:
        try:
            dataset_info = crawl_dataset_docs(url)
            dataset_name = dataset_info['Dataset Name']
            
            # Save individual dataset info
            with open(f'dataset_docs/{dataset_name.lower()}_info.json', 'w', encoding='utf-8') as f:
                json.dump(dataset_info, f, indent=4, ensure_ascii=False)
            
            # Add to complete collection
            all_datasets[dataset_name] = dataset_info
            print(f"Successfully crawled {dataset_name}")
            
        except Exception as e:
            print(f"Error crawling {url}: {str(e)}")
    
    # Save complete collection
    with open('dataset_docs/all_datasets.json', 'w', encoding='utf-8') as f:
        json.dump(all_datasets, f, indent=4, ensure_ascii=False)
    
    return all_datasets

if __name__ == "__main__":
    try:
        result = crawl_all_datasets()
        print("\nCrawling completed. Documentation has been saved to the 'dataset_docs' directory.")
        print(f"Total datasets processed: {len(result)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
