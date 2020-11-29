import urllib.request
import urllib
import requests
from bs4 import BeautifulSoup
import pygsheets
import pandas as pd


#next = soup.find('a', {'aria-label':'Next'})['href']




def load_indeed(job, location):
    '''
    :param job: Job Title
    :param location: Location of Job
    :return: Soup object containing all the jobs on the page
    '''
    # Query parameters
    queries = {'q': job, 'l': location, 'sort': 'date'}

    # Creates URL automatically using urlencode()
    url = ('https://sg.indeed.com/jobs?' + urllib.parse.urlencode(queries))

    page = requests.get(url)
    job_soup = BeautifulSoup(page.content, 'html.parser')
    return job_soup


def extract_job_indeed(listing):
    title = listing.find('a', {'data-tn-element': "jobTitle"})
    title = title.text.strip()
    return title

def extract_company_indeed(listing):
    com = listing.find('span', {"class":"company"})
    com = com.text.strip()
    return com

def extract_link_indeed(listing):
    link = listing.find('a')['href']
    link = 'https://sg.indeed.com/' + link
    return link


def extract_date_indeed(listing):
    date = listing.find('span', class_ = "date ")
    if date:
        date = date.text.strip()
    return date



def extract_job_info_indeed(job_soup):
    full_listings = job_soup.find_all('div', {'data-tn-component': 'organicJob'})

    cols = ['jobs', 'companies', 'links', 'date_listed']
    info = []

    titles = []
    companies = []
    links = []
    date_listed = []
    for listing in full_listings:
        titles.append(extract_job_indeed(listing))
        companies.append(extract_company_indeed(listing))
        links.append(extract_link_indeed(listing))
        date_listed.append(extract_date_indeed(listing))

    info.append(titles)
    info.append(companies)
    info.append(links)
    info.append(date_listed)

    jobs_list = {}
    # Create dictionary with column names as key and the corresponding list of information as values
    for j in range(len(cols)):
        jobs_list[cols[j]] = info[j]

    num = len(info[0])

    print(f'{num} new job listings retrieved.')
    return jobs_list, num


def save_to_gsheets(jobs_list, job_title):
    jobs_df = pd.DataFrame(jobs_list)
    # Authorisation
    gc = pygsheets.authorize(service_file='/Users/kevin/PycharmProjects/WebScrapeTutorial/creds.json')
    # Open the Google Sheets spreadsheet
    sheet = gc.open('Job Search')

    # Select the sheet that corresponds with the particular job title.
    try:
        curr = sheet.worksheet_by_title(job_title)
    except:
        # Create sheet if it hasn't been created
        sheet.add_worksheet(job_title)
        curr = sheet.worksheet_by_title(job_title)

    # Update the sheet with the df supplied as input starting at cell A1 (1, 1)
    curr.set_dataframe(jobs_df, (1, 1))
    print('Done!')

def test_run():
    job_soup = load_indeed('Data Scientist', 'Singapore')

    jobs_list, num = extract_job_info_indeed(job_soup)
    save_to_gsheets(jobs_list, 'Data Scientist')

if __name__ == '__main__':
    test_run()

