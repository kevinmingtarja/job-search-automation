import urllib.request
import urllib
import requests
from bs4 import BeautifulSoup
import pygsheets
import pandas as pd
import re

def load_indeed(job, location):
    # Query parameters
    queries = {'q': job, 'l': location, 'sort': 'date'}

    # Creates URL automatically using urlencode()
    url = ('https://sg.indeed.com/jobs?' + urllib.parse.urlencode(queries))
    print('------------------------------')
    print('Extracting from:')
    print(url)

    page = requests.get(url)
    job_soup = BeautifulSoup(page.content, 'html.parser')
    return job_soup

def get_next_page_link(job_soup):
    try:
        next_ = job_soup.find('a', {'aria-label':'Next'})['href']
        next_ = 'https://sg.indeed.com' + next_
    except:
        next_ = None
    return next_


def extract_job_indeed(listing):
    title = listing.find('a', {'data-tn-element': "jobTitle"})
    title = title.text.strip()
    return title

def extract_company_indeed(listing):
    com = listing.find('span', {"class": "company"})
    com = com.text.strip()
    return com

def extract_link_indeed(listing):
    link = listing.find('a')['href']
    link = 'https://sg.indeed.com' + link
    return link


def extract_date_indeed(listing):
    date = listing.find('span', {'class': 'date'})
    if date:
        date = date.text.strip()
    return date

def extract_requirements_indeed(listing):
    url = extract_link_indeed(listing)
    page = requests.get(url)
    job_soup = BeautifulSoup(page.content, 'html.parser')
    container = job_soup.find('div', {'id': 'jobDescriptionText'})
    # Requirements are usually displayed as list, so we just access the <li> tag
    li = container.find_all('li')
    if li:
        requirements = ''
        for text in li:
            requirements += text.getText()
        return requirements
    return None

def extract_job_info_indeed(job_soup):
    full_listings = job_soup.find_all('div', {'data-tn-component': 'organicJob'})

    titles = []
    companies = []
    links = []
    dates = []
    reqs = []

    for listing in full_listings:
        titles.append(extract_job_indeed(listing))
        companies.append(extract_company_indeed(listing))
        links.append(extract_link_indeed(listing))
        dates.append(extract_date_indeed(listing))
        reqs.append(extract_requirements_indeed(listing))

    return titles, companies, links, dates, reqs


def save_to_gsheets(jobs_list, job_title):
    jobs_df = pd.DataFrame(jobs_list)
    # Authorisation
    gc = pygsheets.authorize(service_file='/Users/kevin/PycharmProjects/WebScrapeTutorial/creds.json')
    # Open the Google Sheets spreadsheet
    sheet = gc.open('Job Search')

    # Select the sheet that corresponds with the particular job title.
    try:
        curr = sheet.worksheet_by_title(job_title.lower())
    except:
        # Create sheet if it hasn't been created
        sheet.add_worksheet(job_title.lower())
        curr = sheet.worksheet_by_title(job_title.lower())

    # Update the sheet with the df supplied as input starting at cell A1 (1, 1)
    curr.set_dataframe(jobs_df, (1, 1))
    print('Done!')


def highlight_red(keywords, job_title):
    # Authorisation
    gc = pygsheets.authorize(service_file='/Users/kevin/PycharmProjects/WebScrapeTutorial/creds.json')
    # Open the Google Sheets spreadsheet
    sheet = gc.open('Job Search')

    curr = sheet.worksheet_by_title(job_title.lower())
    # Gets the values of the 'requirement' column
    reqs = curr.get_values((2, 5), (1000, 5), returnas='matrix', include_tailing_empty=False, include_tailing_empty_rows=False, value_render='UNFORMATTED_VALUE')
    # Iterates through all job requirements and check whether or not it contains any of the keywords
    for row in range(len(reqs)):
        text = reqs[row][0]
        text = re.sub("([a-z])([A-Z])","\g<1> \g<2>", text)
        #curr.update_value((row+2, 5), text, parse=None)
        for word in keywords:
            if word in text:
                row += 2
                for j in range(1, 6):
                    c = curr.cell((row, j))
                    c.color = (1, 0, 0, 0.8) # Red
    return




def main_v1(job_title, location, max_page):
    job_soup = load_indeed(job_title, location)

    # For the dictionary
    cols = ['Job Titles', 'Companies', 'Links', 'Date listed', 'Job requirements']

    titles, companies, links, dates, reqs = extract_job_info_indeed(job_soup)

    # Loops until it reaches end of page, and adds to the list of info each loop.
    num_page = 1
    next_page_link = get_next_page_link(job_soup)

    while next_page_link and num_page < max_page:
        print(next_page_link)
        page = requests.get(next_page_link)
        job_soup = BeautifulSoup(page.content, 'html.parser')
        next_page_info = extract_job_info_indeed(job_soup)
        titles.extend(next_page_info[0])
        companies.extend(next_page_info[1])
        links.extend(next_page_info[2])
        dates.extend(next_page_info[3])
        reqs.extend(next_page_info[4])
        next_page_link = get_next_page_link(job_soup)
        num_page += 1

    print('------------------------------')
    # Make dict for df
    jobs_list = {}
    info = [titles, companies, links, dates, reqs]

    for j in range(len(cols)):
        jobs_list[cols[j]] = info[j]

    num = len(info[0])

    save_to_gsheets(jobs_list, job_title)
    highlight_red(['second year', 'third year', 'final year', 'penultimate'], job_title)
    print(f'{num} entries added.')



if __name__ == '__main__':
    job_title = input('Job Title: ')
    location = input('Location: ')
    max_page = input('Maximum Pages: ')
    main_v1(job_title, location, int(max_page))

