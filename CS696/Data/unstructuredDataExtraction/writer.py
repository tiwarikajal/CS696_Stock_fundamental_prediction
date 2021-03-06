from os import listdir, mkdir
from os.path import isfile, join, isdir
import csv
import utils
from sectionExtraction import SectionExtraction, FilingsDownloader
import pandas as pd
import requests
import logging
import re
from collections import defaultdict
logger = logging.getLogger('structured')

exceptions = {'Brookfield Property REIT Inc Class A':1496048, 'Liberty Media Corporation Series A Liberty Formula One':1560385, 'Vistra Energy Corp.':1692819 , 'IAA, Inc.':1745041, 'Gardner Denver Holdings, Inc.':1699150}

foldername = 'datalinks'

def startWriting(downloadPath, tickerList, fieldnames,links=True,latest=10, index=0,  sections=["item1a", "item7"], doc_type = "10-K"):
    if links:
        startWritingUsingLinks(downloadPath, tickerList, fieldnames, index=0, sections=["item1a", "item7"], doc_type = "10-K")
    else:
        startWritingUsingDownloads(downloadPath, tickerList, fieldnames,latest=10,index=0,  sections=["item1a", "item7"], doc_type = "10-K")


def startWritingUsingDownloads(downloadPath, tickerList, fieldnames,index=0, latest=10, sections=["item1a", "item7"], doc_type = "10-K"):
    ''' Get List of all the folders concatenated with its relative path '''
    companyLessthan10 = []
    companyWithNoData = []
    erroneousCompanies = []
    fieldnames.extend(sections)
    dataStats = {}
    df = pd.read_csv(tickerList)
    ''' SEC-Edgar module creates a folder 'sec_edgar_filings' in which it downloades the filings '''
    newPath = join(downloadPath, "sec_edgar_filings")
    companyFilingsPath = ""
    
    ''' Create data folder where company csv(s) will be stored'''
#     os.mkdir(path)
    dataPath = join(downloadPath, foldername)
    if not isdir(dataPath):
        mkdir(dataPath)
    ''' loop through all folders i.e. companies '''
    downloader = FilingsDownloader(downloadPath)
    for i in range(index, len(df)):
        row = df.iloc[i]

#         try:

        ''' Download latest 10 filings for the Company '''
        logger.info("Downloading {} latest Filings for {}".format(latest, row["Company Name"]))
        try:
            downloader.downloadFilings(ticker=row['Ticker'],filing_type=doc_type, latest = latest)
        except Exception as e:
            continue
        dataStats[row["Ticker"]] = {"totalfilings":0,"years":[]}
        for sec in sections:
            dataStats[row["Ticker"]][sec] = []
        ''' SEC-Edgar module creates a subfolder named by the company ticker inside 'sec_edgar_filings'
            Therfore join the path  '''
        companyFilingsPath = join(newPath, row['Ticker'], doc_type)
#         print("companyfilingsPath {}".format(companyFilingsPath))


        ''' Sanity Check: if the files are downloaded '''
        if not isdir(companyFilingsPath):
            logger.info("No filings Downloaded for {}".format(row["Company Name"]))
            companyWithNoData.append(row["Company Name"])
            continue


        ''' List downloded filing path and file names '''
        companyFilings = [(join(companyFilingsPath, f), f) for f in listdir(companyFilingsPath)]
        dataStats[row["Ticker"]]["totalfilings"] = len(companyFilings)

        writers = utils.createCSVWriters(dataPath, fieldnames, num=1, filename=row['Ticker'])
        ''' Log the companies having less than 10 recent filings '''
        if len(companyFilings) <latest:
            companyLessthan10.append(row["Company Name"])



        ''' Extract Section from each filings '''
        for filing in companyFilings:
            extractor = SectionExtraction(doc_type)

            line = utils.formLine(fieldnames)
            line["Company"] = row["Company Name"]
            line["Industry"] = row["Industry"]
            line["Top 100"] = row["Top 100"] if "Top 100" in row else "N/A"
            ''' Get filing path and filing path '''
            filingPath, filingName = filing

            f = open(filingPath,'r',encoding="utf8")
            textdata = f.read()
            f.close()

            ''' Get year of the filling from the filing name '''
            ''' file name ex "0001283630-16-000038.txt", 2016 represents year in which 10k was filed and it was for year 2015 '''
            filingName = filingName.split("-")
            line["Year"] = int(filingName[1])-1 + 2000
            #writer_index = int(filingName[1])-10
            try:
                sectionList = extractor.extractHTMLSections(textdata)
            except Exception as e:
                for item in sections:
                    line[item] = e
                writers[0][0].writerow(line)
                continue
            dataStats[row["Ticker"]]["years"].append(line["Year"])
            ''' Extracting Sections  '''
            for item in sections:
                try:
                    if item in sectionList:
                        line[item] = extractor.extractTextFromSection(key =item)
                    else:
                        logger.info(" {} not in section list for Company Name: {}, path: {}".format(item, row["Company Name"], filing))
                    if item not in dataStats[row["Ticker"]].keys():
                            dataStats[row["Ticker"]][item] = []
                    dataStats[row["Ticker"]][item].append(len(line[item]))
                    if len(line[item]) <100:
                        logger.info("empty text, Company Name: {}, filing:{} ".format(row["Company Name"], filing))
                        line[item] = "CustomError: " + line[item]

                    logger.info("Extracted {} Length:{}".format(item,len(line[item])))
                except Exception as e:
#                     erroneousCompanies.append((e, row["Company Name"]))
                    line[item] = e
                    dataStats[row["Ticker"]][item].append(0)
                    continue
            ''' write to csv file '''
           
            #if writer_index <0 or writer_index>=11:
            #    logger.info("Problem with the writer Index: {}, filingsName:{}".format(writer_index, filingName))
            #    continue

            writers[0][0].writerow(line)
        downloader.removefilings(join(newPath, row['Ticker']))
        utils.closeWriters(writers)
    return companyLessthan10, companyWithNoData, erroneousCompanies,dataStats




def startWritingUsingLinks(downloadPath, tickerList, fieldnames, index=0, sections=["item1a", "item7"], doc_type = "10-K"):
    ''' Get List of all the folders concatenated with its relative path '''
    fieldnames.extend(sections)
    df = pd.read_csv(tickerList)
    dataStats = {}
    ''' Create data folder where company csv(s) will be stored'''
    dataPath = join(downloadPath, foldername)
    if not isdir(dataPath):
        mkdir(dataPath)
    for i in range(index, len(df)):
        row = df.iloc[i]
        ''' Download latest 10 filings for the Company '''
        logger.info("Downloading Link: {}  Filings for {}, year:{}".format(row["Form10KLink"], row["Ticker"],row["FilingDate"]))
        writers = []
        date = row["FiscalPeriodEnd"].split("/")
        year = int(date[2])-1
        if isfile(join(dataPath,row['Ticker']+".csv")):
            f = open(join(dataPath,row['Ticker']+".csv"), mode='w+', encoding="utf-8", newline='')
            reader = csv.DictReader(f)
            foundYear = False
            for csvrow in reader:
                if csvrow["Year"] == year:
                    for item in sections:
                        foundYear = True
                        if not len(csvrow["item"])<100:
                            foundYear = False
                            break
              
            if not foundYear:                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writers.append([writer,f])
            else:
                continue
        else:
            writers = utils.createCSVWriters(dataPath, fieldnames, num=1, filename=row['Ticker'])
        try:
            link = row["Form10KLink"]
            link = re.sub('\/(ix\?doc=)\/', '//', link)
            r_obj = requests.get(link)
            textdata = str(r_obj.content)
        except Exception as e:
            continue
        line = utils.formLine(fieldnames)
        line["CIK"] = row["CIK"]
        line["Form10KName"] = row["Form10KName"]
        line["IndexLink"] = row["IndexLink"]
        line["DocIndex"] = row["DocIndex"]
        line["Description"] = row["Description"]
        date = row["FiscalPeriodEnd"].split("/")
        line["Year"] = year

        extractor = SectionExtraction(doc_type)
        try:
            sectionList = extractor.extractHTMLSectionsFromLinks(textdata)
        except Exception as e:
            continue
        ''' Extracting Sections  '''
        for item in sections:
            try:
                if item in sectionList:
                    line[item] = extractor.extractTextFromSection(key =item)
                else:
                    logger.info(" {} not in section list for Company Name: {}, path: {}".format(item, row["Ticker"], row["Form10KLink"]))
                if len(line[item]) <100:
                    line[item] = ""
                    logger.info("empty text, Company Name: {}, filing:{} ".format(row["Ticker"], row["10KLink"]))
                else:
                    if row["Ticker"] not in dataStats.keys():
                        dataStats[row["Ticker"]] = defaultdict(int)
                    dataStats[row["Ticker"]][item] +=1
                logger.info("Extracted {} Length:{}".format(item,len(line[item])))
            except Exception as e:
                line[item] = ""
                continue
        ''' write to csv file '''
        writers[0][0].writerow(line)
        utils.closeWriters(writers)
    return dataStats
