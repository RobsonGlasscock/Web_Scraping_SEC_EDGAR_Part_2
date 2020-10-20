import pandas as pd
from bs4 import BeautifulSoup
import numpy as np
import requests

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

################################ Attributions #########################################

# https://towardsdatascience.com/value-investing-dashboard-with-python-beautiful-soup-and-dash-python-43002f6a97ca
# https://www.codeproject.com/Articles/1227268/Accessing-Financial-Reports-in-the-EDGAR-Database
# "Python and Web Data Extraction: Introduction" by Alvin Zuyin Zheng
# "Scraping EDGAR with Python" by Rasha Ashraf, Journal of Education for Business
# https://stackoverflow.com/questions/47736600/how-to-get-a-value-from-a-text-document-that-has-an-unstructured-table
# https://stackoverflow.com/questions/2010481/how-do-you-get-all-the-rows-from-a-particular-table-using-beautifulsoup
# https://www.youtube.com/watch?v=gfpmKkxhb9M
# https://www.youtube.com/watch?v=XQgXKtPSzUI
# "Pandas for Everyone: Python Data Analysis" by Daniel Y. Chen
# https://www.crummy.com/software/BeautifulSoup/bs4/doc/
# "Python for Data Analysis" by Wes McKinney
# "Pandas Cookbook" by Theodore Petrou
# "Python Data Science Handbook" by Jake VanderPlas
# "Think Python" by Allen B. Downey
# https://realpython.com/
# Kevin Markham's Data School: https://www.youtube.com/watch?v=zXif_9RVadI

############################### Attributions ##########################################

# link to FCCY's 12/31/2017 10-K in html format.
# https://www.sec.gov/ix?doc=/Archives/edgar/data/1141807/000114180718000005/fccy-20171231x10k.htm

# link to all EDGAR filings
# https://www.sec.gov/Archives/edgar/full-index/
# select a year, then quarter, then master.idx which you will open with a text editor.
# you can see there are various filings (10-K, 10-Q, ). Iterating through each of these fillings can also be automated.

# Open FCCY's 12/31/2017 10-K
u = requests.get('https://www.sec.gov/Archives/edgar/data/1141807/000114180718000005/0001141807-18-000005.txt')

soup = BeautifulSoup(u.text, 'html.parser')

# Below includes spans and tables.
results= soup.find_all(['span', 'table'])

len(results)

# Find where the auditor's report(s) is. The financial statements will be after the auditor's report and before the beginning of the notes to the financial statements. There is substantial variation in the titles contained in various 10-K's. One approach is to condition on the various combinations of titles and look for those directly, but I opted to use the structure of the 10-K to narrow down the tables to only include the financial statements, and then to identify each financial statement based on the account names typically found within that financial statement.

# Condition where the audit report is.
position_audit= []
for i, j in enumerate(results):
        if "report of independent registered public accounting firm" in j.text.lower():
            position_audit.append(i)

position_audit

lower_bound= max(position_audit)

# Find start of the notes to the financial statements
position_notes= []
notes_text= []
for i, j in enumerate(results):
        if "notes to consolidated financial statements" in j.text.lower():
            position_notes.append(i)
            notes_text.append(j)

# The structure of the beginning of the notes has the company name, then the word 'notes', then the time period. I exploit that below. The list with the various month-ends is so that this generalizes to non-fiscal year end entities.
months= ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']
for i in position_notes:
    for j in months:
        if j in results[i+1].text.lower():
            print(i)
            upper_bound=i

# The approximate boundaries to the financial statements are 9265 and 11478. I modify the results set to include the content between the upper and lower bounds above. These are the only parts of the 10-K we care about.
financial_statements= results[lower_bound:upper_bound]

# Read the file out as text so I can then read it back in and use pd.read_html() to pull the tables. Need to convert the list objects to strings prior to writing out. There is probably a better way to do this, but this works for now.
with open('financial_statements.txt', 'w') as fn:
    for item in financial_statements:
        fn.write(str(item))


content = open('financial_statements.txt', 'r').read()


tables2= pd.read_html(content)
len(tables2)

# It should seem strange that there are 9 tables in this 10-K. The financial statements typically consist of the balance sheet, income statement, statement of cash flows, and statement of changes in owners' equity. Depending on the types of transactions firms engage in, there may also be a comprehensive income statement. That's five total financial statements, but FCCY's 10-K contains 9 tables in the financial statement section. Let's explore that below.

tables2[0]
# The first table is the balance sheet.
tables2[1]
# The second table is the income statement.
tables2[2]
# The third table is the comprehensive income statement.
tables2[3]
# The fourth element is actually a note at the bottom of the comprehensive income statement. This is not a financial statement.
tables2[4]
# Same as above.
tables2[5]
# Same as above.
tables2[6]
#  The seventh table is the statement of changes in owners' equity.

tables2[7]
# The eight table is part of the statement of cash flows. FCCY's statement of cash flows is split across two different pages and has been split across two different tables.
tables2[8]
# The ninth element is the portion of the statement of cash flows that is on the split page.

# The order of the financial statements will differ across companies, so below we identify each financial statement based on a cumulative count of some account titles that typically show up on that financial statement. This will also eliminate the notes that were tagged as tables (the fourth, fifth, and sixth elements shown above).


df_temp= pd.DataFrame(tables2[0]).copy()

# Balance Sheet #########################
marker=0
keys= []
values= []
for e,j in enumerate(tables2):
    df_temp= pd.DataFrame(tables2[e]).copy()
    try:
        # Condition on first column being a pandas object which contains the account titles.
        if df_temp[0].dtypes=='O':
        # CIK 1007019 has extra spaces between the account titles so .sum() below returns no hits. To avoid this, first remove all of the spaces between the words in the account titles. Also, ignore case since capitalization conventions will vary across firms.
            df_temp[0]= df_temp[0].str.replace(' ', '')
            t=df_temp[0].str.match("assets|totalassets|totalliabilities|liabilities|liabilitiesandshareholders'equity|shareholder'sequity|stockholders'equity|liabilitiesandstockholders'equity|totalstockholders'equity|totalliabilities,redeemableconvertiblepreferredstock,andstockholders'equity|retainedearnings|retainedearnings(deficit)|accumulated othercomprehensiveincome|accumulatedothercomprehensiveincome(loss)|additionalpaidincapital|additionalpaid-incapital|stockholders'equity(deficiency)|noncontrollinginterests", case=False).sum()
            keys.append(e)
            values.append(t)
        else:
            continue
    except Exception:
        continue

dict= dict(zip(keys, values))
marker= max(dict, key=dict.get)
del dict

tables2[marker]

# No exceptions noted. p/f/r.

# Income Statement
marker=0
keys= []
values= []
for e,j in enumerate(tables2):
    df_temp= pd.DataFrame(tables2[e]).copy()
    try:
        # Condition on first column being a pandas object which contains the account titles.
        if df_temp[0].dtypes=='O':
        # CIK 1007019 has extra spaces between the account titles so .sum() below returns no hits. To avoid this, first remove all of the spaces between the words in the account titles. Also, ignore case since capitalization conventions will vary across firms.
            df_temp[0]= df_temp[0].str.replace(' ', '')
            t=df_temp[0].str.match("netincome|incometaxes|otherincome|netincomepercommonshare|basic|diluted|weightedaveragesharesoutstanding", case=False).sum()
            keys.append(e)
            values.append(t)
        else:
            continue
    except Exception:
        continue

dict= dict(zip(keys, values))
marker= max(dict, key=dict.get)
del dict

marker
tables2[marker]

# No exceptions noted.

# Owners Equity Statement #######
marker=0
keys= []
values= []
for e,j in enumerate(tables2):
    df_temp= pd.DataFrame(tables2[e]).copy()
    try:
        # Condition on first column being a pandas object which contains the account titles.
        if df_temp[0].dtypes=='O':
        # CIK 1007019 has extra spaces between the account titles so .sum() below returns no hits. To avoid this, first remove all of the spaces between the words in the account titles. Also, ignore case since capitalization conventions will vary across firms.
            df_temp[0]= df_temp[0].str.replace(' ', '')
            t=df_temp[0].str.match("share-basedcompensation|dividends|stockoptions", case=False).sum()
            keys.append(e)
            values.append(t)
        else:
            continue
    except Exception:
        continue

dict= dict(zip(keys, values))
marker= max(dict, key=dict.get)
del dict

marker
tables2[marker]

# OCI Statement ################
marker=0
keys= []
values= []
for e,j in enumerate(tables2):
    df_temp= pd.DataFrame(tables2[e]).copy()
    try:
        # Condition on first column being a pandas object which contains the account titles.
        if df_temp[0].dtypes=='O':
        # CIK 1007019 has extra spaces between the account titles so .sum() below returns no hits. To avoid this, first remove all of the spaces between the words in the account titles. Also, ignore case since capitalization conventions will vary across firms.
            df_temp[0]= df_temp[0].str.replace(' ', '')
            t=df_temp[0].str.match("othercomprehensiveincome(loss)|comprehensiveincome|totalothercomprehensiveincome|totalothercomprehensiveloss", case=False).sum()
            keys.append(e)
            values.append(t)
        else:
            continue
    except Exception:
        continue

dict= dict(zip(keys, values))
marker= max(dict, key=dict.get)
del dict

marker
tables2[marker]

# No exceptions noted.

# SOCF ###############
marker=0
keys= []
values= []
for e,j in enumerate(tables2):
    df_temp= pd.DataFrame(tables2[e]).copy()
    try:
        # Condition on first column being a pandas object which contains the account titles.
        if df_temp[0].dtypes=='O':
        # CIK 1007019 has extra spaces between the account titles so .sum() below returns no hits. To avoid this, first remove all of the spaces between the words in the account titles. Also, ignore case since capitalization conventions will vary across firms.
            df_temp[0]= df_temp[0].str.replace(' ', '')
            t=df_temp[0].str.match("operating|investing|financing", case=False).sum()
            keys.append(e)
            values.append(t)
        else:
            continue
    except Exception:
        continue

dict= dict(zip(keys, values))
dict
marker= max(dict, key=dict.get)
del dict

marker
tables2[marker]

# Since FCCY splits the statement of cash flows into two tables, only the first table meets the logical conditions of the code via the maximum. I'm not sure 1) how frequently tables are split across pages or 2) how the code could be modified in a systematic way to capture both parts of tables for entities with split financial statements. I may look into this in the future if it appears to cause systematic problems.

tables2_ref= tables2[0].copy()

# Drop null rows.
tables2[0].dropna(how='all', inplace=True)


# The next step is to turn this into a useable dataframe. You can see above that there are multiple columns in the table. The structure contains three columns for 2017, a null column, and then three columns for 2016. Negative numbers begin with "(" and the closing ")" is in the third column for each year. The columns that we want are the ones that contain the fewest null values.

col_count=tables2[0].notnull().sum()
col_count

# Column 0 has the account titles, columns 1 and 2 contain the 2017 numbers, and columns 5 and 6 contain the 2016 numbers. Note that columns 1 and 2 and 5 and 6 typically contain duplicates. Columns 1 and 5 also sometimes contain a dollar sign "$". We need to remove the duplicates and only keep one column for each year. But we also need to be aware that the dollar signs are not nulls, so the count of non-null values in the columns with and without dollar signs is the same. To deal with this, we reset the $'s equal to NaN's and then re-count the number of missing values.

tables2[0].replace({'$': np.nan}, inplace=True)

col_count=tables2[0].notnull().sum()
col_count


# Replace column 0, which is the account titles, to 0. This column has even more non-missing values than the account balances so I don't want the maximum to condition on this. I'm looking for the second highest non-missing columns since these are the account balances.
col_count[0]= 0
col_count

# Boolean series for which columns have the most non-missing values.
col_index =col_count== col_count.max()
col_index

# Can see above that the 3rd and 6th columns are the ones with the account balances. But later I also want column 0 with the account names, so below I manually change the 0th index back to True.
col_index[0]=True

bsheet= tables2[0].copy()

bsheet= bsheet.loc[:, col_index]

# Identify and drop header rows on the balance sheet without corresponding numbers (e.g., ASSETS, LIABILITIES AND SHAREHOLDERS' EQUITY, etc.)
dropper= (bsheet[bsheet.columns[-1]].notnull()) & (bsheet[bsheet.columns[-2]].notnull())
dropper
bsheet= bsheet[dropper]


bsheet= bsheet.transpose()
bsheet.reset_index(inplace= True, drop=True)

# Make the 0th row the column names of the DataFrame.
bsheet.columns= bsheet.loc[0]

bsheet.drop(0, inplace=True)
bsheet

# Pull in the CIK from the url into the dataframe.
url= 'https://www.sec.gov/Archives/edgar/data/1141807/000114180718000005/0001141807-18-000005.txt'
start= 'https://www.sec.gov/Archives/edgar/data/'
# remove above then keep everything until / and that will be the cik.
url2= url.replace(start,'')
url2
sep= '/'
# split on seperator one time, and keep the fist element.

cik= url2.split(sep)[0]
cik

bsheet['CIK']= int(cik)

# Rename the null column to Year.
bsheet.rename(columns={bsheet.columns[0]:'Year'}, inplace=True)

# Set the multi-index.
bsheet.set_index(['CIK', 'Year'], inplace=True)

# Next, convert the strings into integers. Per visual inspection, need to deal with three issues 1) leading ( for negative numbers, 2) pulling commas out of each string and 3) — for values of 0.
bsheet=bsheet.apply(lambda x: x.str.replace('(', '-'))
bsheet= bsheet.apply(lambda x: x.str.replace(',', ''))
bsheet

# can see above that variables with 0 values have a dash-type character.
bsheet['Other Real Estate Owned'].value_counts()
bsheet= bsheet.apply(lambda x: x.str.replace('—', '0'))
bsheet

# Convert strings to integers
bsheet= bsheet.apply(lambda x: pd.to_numeric(x))
bsheet
bsheet.info()