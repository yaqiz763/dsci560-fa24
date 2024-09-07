import requests
from urllib.parse import urljoin
import os
import pdfplumber
import pandas as pd
from bs4 import BeautifulSoup


def find_pdf_links(url):
    # Send a request to the webpage
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code != 200:
        print(f"Failed to access {url}. Status code: {response.status_code}")
        return []

    # Parse the webpage content using BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Search for all links that point to a PDF file
    pdf_links = []
    for link in soup.find_all("a", href=True):
        href = link['href']
        # Check if the link ends with ".pdf"
        if href.lower().endswith(".pdf"):
            # Convert to absolute URL if needed
            full_url = urljoin(url, href)
            pdf_links.append(full_url)
    
    print(f"Found {len(pdf_links)} PDF links on the webpage.")
    for pdf in pdf_links:
        print(pdf)

    return pdf_links


def get_data_directory():
    file_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(file_dir)
    data_dir = os.path.join(root_dir, "data")

   
    # Create the directory if it doesn't exist
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    return data_dir


def download_pdf(url, file_path):
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        with open(file_path, "wb") as file:
            file.write(response.content)
        print(f"\nPDF downloaded and saved as {file_path}")
    else:
        print(f"Failed to download PDF. Status code: {response.status_code}")


def extract_table(pdf_path, csv_path):
    all_tables = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num in range(2,22):  
            page = pdf.pages[page_num]
            table = page.extract_table()
            
            if table:
                data_rows = table[3:]  # skip header rows

                # Convert the table to DataFrame
                df = pd.DataFrame(data_rows)

                # Extract relevant columns
                df = df.iloc[:, :6] 

                # Rename columns
                df.columns = ["Country", 
                              "Population (millions) mid-2023", 
                              "Births per 1,000 Population", 
                              "Deaths per 1,000 Population", 
                              "Rate of Natural Increase (%)", 
                              "Net Migration Rate"]

                # Replace empty strings with None across the DataFrame
                df.replace("", None, inplace=True)

                # Forward-fill 'Country' column to propagate country names
                df["Country"] = df["Country"].ffill()

                # Drop rows with any None or NaN values across all columns
                df.dropna(how='any', inplace=True)

                # Add the cleaned DataFrame to the list of all tables
                all_tables.append(df)

                print(f"Extracted table from page {page_num + 1}")
            else:
                print(f"No table found on page {page_num + 1}")

    # Combine all tables into a single DataFrame and save as CSV
    if all_tables:
        combined_df = pd.concat(all_tables, ignore_index=True)
        combined_df.reset_index(drop=True, inplace=True)
        
        # Save combined data to CSV
        combined_df.to_csv(csv_path, index=False)
        print(f"Data saved to {csv_path}")
    else:
        print("No tables were found in the PDF.")

def display_data(file_path):
    # Load the dataset
    df = pd.read_csv(file_path)
    
    print("\n##########################################################")
    # Display a few sample records
    print("Last few records:\n", df.tail())
    
    # Calculate the size and dimensions of the dataset
    print("\nSize of the dataset (number of elements in object):", df.size)
    print("Dimensions of the dataset (row, column):", df.shape)
    
    # Identify missing data
    missing_data = df.isnull().sum()
    print("\nMissing data in each column:\n", missing_data)
    
    # Column data types
    print("\nData types of each column:\n", df.dtypes)
    print("##########################################################")

# Main execution
if __name__ == "__main__":

    pdf_files = find_pdf_links("https://repository.gheli.harvard.edu/repository/11620/")

    for link in pdf_files:
        if "population" in link.lower():
            url = link
            break

    data_dir = get_data_directory()
    pdf_file_path = os.path.join(data_dir, "raw_data", "population_data.pdf")
    csv_file_path = os.path.join(data_dir, "processed_data", "population_data.csv")
    
    # Download the PDF and save it to the specified location
    download_pdf(url, pdf_file_path)
    
    # Extract tables from all pages of the PDF, clean the data, and save as CSV
    extract_table(pdf_file_path, csv_file_path)

    # Display the data with basic operations
    display_data(csv_file_path)
