#!/usr/bin/env python3


import sys
if sys.version_info[0] != 3:
    sys.exit("Sorry, only Python 3 is supported by this script.")

import os
from os.path import join, exists
from bs4 import BeautifulSoup
import re



def open_ec(filepath):
    '''
    Open the EC html file that should be parsed.
    Return a soup instance.
    '''
    with open(filepath, 'r', encoding='ISO-8859-1') as f:
        soup = BeautifulSoup(f, 'html.parser')
    return soup


class _BrendaBaseClass(object):
    '''
    Base class intended for subclassing.
    '''
    def __init__(self, soup_instance):
        self.soup = soup_instance


    def _parse(self):
        '''
        Perform the parsing
        '''
        self.grey1_data, self.grey2_data, self.hiddengrey1_data, self.hiddengrey2_data = self._get_table_divs()


    def _normalize_name(self, organism):
        '''
        Normalize a single organism name.
        Ignore strain designations.
        Should be: "Escherichia coli"
        '''
        assert type(organism) is str, 'Error, the organism names must be supplied as strings. The input "%s" is not.' % organism

        # deal with organism names separated by _
        if len(organism.split()) < len(organism.split('_')):
            organism = ' '.join(organism.split('_'))

        # take only the first two parts of the name
        organism = ' '.join(organism.split()[:2])

        return organism.lower().capitalize()


    def _parse_single_div(self, div):
        '''
        Each div needs to be parsed differently, depending on the target table.
        '''
        raise NotImplementedError


    def _split_divs(self, div_data):
        '''
        Each table needs to have its own parsing of the table divs.
        This is the method where that should be implemented.
        '''
        raise NotImplementedError


    def _get_table_divs(self):
        '''
        Find the relevant table divs
        '''

        #isolate the table with the given ID
        table = self.soup.find("div", { "id" : self.table_id })
        if table is None:
            return None, None, None, None
        else:
            #print([s.get_text() for s in table.find_all("div", { "class" : "header" })])
            assert any([self.table_name in s.get_text() for s in table.find_all("div", { "class" : "header" })]), 'Something is wrong with %s' % self.table_name

            mydivs_grey1 = table.find_all("div", { "class" : "row rgrey1" })
            grey1_data = self._split_divs(mydivs_grey1)

            mydivs_grey2 = table.find_all("div", { "class" : "row rgrey2" })
            grey2_data = self._split_divs(mydivs_grey2)

            mydivs_hiddengrey1 = table.find_all("div", { "class" : "hidden rgrey1" })
            hiddengrey1_data = self._split_divs(mydivs_hiddengrey1)

            mydivs_hiddengrey2 = table.find_all("div", { "class" : "hidden rgrey2" })
            hiddengrey2_data = self._split_divs(mydivs_hiddengrey2)

            return grey1_data, grey2_data, hiddengrey1_data, hiddengrey2_data



class _ThreeLevelDiv(_BrendaBaseClass):
    '''
    The divs have different "depths", different number of cells before I get to the UNIPROT ID.
    This class can parse divs that has a depth of three.
    "numeric" determines whether the first value in the table is expected to be numeric or not.
    The expcted structure is "value, organism, uniprot_id"
    '''
    def __init__(self, soup_instance, numeric):
        _BrendaBaseClass.__init__(self, soup_instance)
        self.numeric = numeric


    def _parse_single_div(self, div):
        '''
        Extract the data from a single div
        '''
        #there is an issue of the comments being appended to the last uniprot id
        #need to parse the div twice, in two different ways to be able to filter
        #out thse comments

        #first make a list of potential uniprot ids
        #critically these do not contain the comments
        potential = []
        for item in div.find_all("a"):
            potential.append(item.get_text())
        potential = list(filter(None, potential))

        #get all div text
        text = div.get_text(',')
        if len(text.split('\n')) > 3:
            parts = text.split('\n')

            #get value
            value = parts[1].strip(',')
            value = value.replace(' ', '')

            # if value is numeric, convert to float, take average if nessecary
            if self.numeric is True:
                try:
                    value = float(value)
                except:
                    if len(value.split('-')) == 2:
                        a, b = value.split('-')
                        # sometimes a number is given together with additional information
                        # "0.018-additionalinformation", need to catch this exception
                        if a == ',additionalinformation' or b == ',additionalinformation':
                            return None
                        value = round((float(a)+float(b))/2)
                    elif len(value.split('to')) == 2:
                        a, b = value.split('to')
                        value = round((float(a)+float(b))/2)
                    elif value == 'additionalinformation':
                        return None
                    else:
                        print(value)
                        raise ValueError

            if value == 'additionalinformation':
                return None

            #get organism
            organism = parts[2].strip(',')
            organism = self._normalize_name(organism)

            #get a list of the uniprot ids, filter out comments and such by matching to the potential ones
            uniprot_id_list = re.split(',|and', parts[3].replace(' ', '').replace(';', '').replace('-', ''))
            uniprot_id_list = [s for s in uniprot_id_list if s in potential]
            if uniprot_id_list == ['']:
                return None
            else:
                #print(value, organism, uniprot_id_list)
                return value, organism, uniprot_id_list
        else:
            return None


    def _split_divs(self, divs):
        '''
        Take the html section and parse out all divs
        '''
        all_data = {}
        for div in divs:

            #parse the div
            result = self._parse_single_div(div)
            if result is None:
                continue

            #get data from the div
            value, organism, uniprot_id_list = result

            #add to data structure
            if all_data.get(organism) is None:
                all_data[organism] = {}

            for uniprot_id in uniprot_id_list:
                if all_data[organism].get(uniprot_id) is None:
                    all_data[organism][uniprot_id] = []
                all_data[organism][uniprot_id].append(value)

        return all_data


    def get_data(self):
        '''
        Extract the section of the HTML code that corresponds to the desired table.
        Then parse it and combine all the data.
        '''

        if self.grey1_data == None and self.grey2_data == None and self.hiddengrey1_data == None and self.hiddengrey2_data == None:
            return None

        else:
            #combine the two datasets
            found_at_least_one_uniprot_id = False
            combined_data = {}
            for data in [self.grey1_data, self.grey2_data, self.hiddengrey1_data, self.hiddengrey2_data]:
                for organism in data.keys():
                    if data[organism] != {}:
                        if combined_data.get(organism) is None:
                            combined_data[organism] = {}

                        for uniprot_id in data[organism].keys():
                            if combined_data[organism].get(uniprot_id) is None:
                                combined_data[organism][uniprot_id] = []
                            found_at_least_one_uniprot_id = True
                            combined_data[organism][uniprot_id].extend(data[organism][uniprot_id])

            if found_at_least_one_uniprot_id is True:
                return combined_data
            else:
                return None



class _FourLevelDiv(_BrendaBaseClass):
    '''
    The divs have different "depths", different number of cells before I get to the UNIPROT ID.
    This class can parse divs that has a depth of four.
    "numeric" determines whether the first value in the table is expected to be numeric or not.
    The expcted structure is "value, information, organism, uniprot_id"
    '''
    def __init__(self, soup_instance, numeric):
        _BrendaBaseClass.__init__(self, soup_instance)
        self.numeric = numeric


    def _parse_single_div(self, div):
        '''

        '''
        #there is an issue of the comments being appended to the last uniprot id
        #need to parse the div twice, in two different ways to be able to filter
        #out thse comments

        #first make a list of potential uniprot ids
        #critically these do not contain the comments
        potential = []
        for item in div.find_all("a"):
            potential.append(item.get_text())
        potential = list(filter(None, potential))

        #get all div text
        text = div.get_text(',')
        if len(text.split('\n')) > 3:
            parts = text.split('\n')
            #print(parts)

            #get value value
            value = parts[1].strip(',')
            value = value.replace(' ', '')

            # if value is numeric, convert to float, take average if nessecary
            if self.numeric is True:
                try:
                    value = float(value)
                except:
                    if len(value.split('-')) == 2:
                        a, b = value.split('-')
                        # sometimes a number is given together with additional information
                        # "0.018-additionalinformation", need to catch this exception
                        if a == ',additionalinformation' or b == ',additionalinformation':
                            return None
                        value = round((float(a)+float(b))/2)
                    elif len(value.split('to')) == 2:
                        a, b = value.split('to')
                        value = round((float(a)+float(b))/2)
                    elif value == 'additionalinformation':
                        return None
                    else:
                        print(value)
                        raise ValueError

            if value == 'additionalinformation':
                return None

            # get the info cell
            information = parts[2].strip(',')

            #get organism
            organism = parts[3].strip(',')
            organism = self._normalize_name(organism)

            #get a list of the uniprot ids, filter out comments and such by matching to the potential ones
            uniprot_id_list = re.split(',|and', parts[4].replace(' ', '').replace(';', '').replace('-', ''))
            uniprot_id_list = [s for s in uniprot_id_list if s in potential]
            #print(uniprot_id_list)

            if uniprot_id_list == ['']:
                return None
            else:
                #print(value, organism, uniprot_id_list)
                return value, information, organism, uniprot_id_list
        else:
            return None


    def _split_divs(self, divs):
        '''
        Take the html section and parse out all divs
        '''
        all_data = {}
        for div in divs:

            #parse the div
            result = self._parse_single_div(div)
            if result is None:
                continue

            value, information, organism, uniprot_id_list = result

            #add to data structure
            if all_data.get(organism) is None:
                all_data[organism] = {}

            for uniprot_id in uniprot_id_list:
                if all_data[organism].get(uniprot_id) is None:
                    all_data[organism][uniprot_id] = {}

                if all_data[organism][uniprot_id].get(information) is None:
                    all_data[organism][uniprot_id][information] = []

                all_data[organism][uniprot_id][information].append(value)

        return all_data


    def get_data(self):
        '''
        Extract the section of the HTML code that corresponds to the value
        '''

        if self.grey1_data == None and self.grey2_data == None and self.hiddengrey1_data == None and self.hiddengrey2_data == None:
            return None

        else:
            #combine the two datasets
            found_at_least_one_uniprot_id = False
            combined_data = {}
            for data in [self.grey1_data, self.grey2_data, self.hiddengrey1_data, self.hiddengrey2_data]:
                for organism in data.keys():
                    if data[organism] != {}:
                        if combined_data.get(organism) is None:
                            combined_data[organism] = {}

                        for uniprot_id in data[organism].keys():
                            if combined_data[organism].get(uniprot_id) is None:
                                combined_data[organism][uniprot_id] = {}

                            for information in data[organism][uniprot_id].keys():
                                if combined_data[organism][uniprot_id].get(information) is None:
                                    combined_data[organism][uniprot_id][information] = []
                                found_at_least_one_uniprot_id = True
                                combined_data[organism][uniprot_id][information].extend(data[organism][uniprot_id][information])

            if found_at_least_one_uniprot_id is True:
                return combined_data
            else:
                return None




class Organism(_BrendaBaseClass):
    '''
    Parsing the ORGANISM table in BRENDA.
    It's kind of a special case so I don't use subclassing of the other LevelDiv classes.
    '''
    def __init__(self, soup_instance):
        _BrendaBaseClass.__init__(self, soup_instance)

        self.table_name = 'ORGANISM'
        self.table_id = 'tab20'
        self._parse()


    def _parse_single_div(self, div):
        '''
        '''

        #there is an issue of the comments being appended to the last uniprot id
        #need to parse the div twice, in two different ways to be able to filter
        #out thse comments

        #first make a list of potential uniprot ids
        #critically these do not contain the comments
        potential = []
        for item in div.find_all("a"):
            potential.append(item.get_text())
        potential = list(filter(None, potential))

        #get all div text
        text = div.get_text(',')
        if len(text.split('\n')) > 3:
            parts = text.split('\n')

            #get organism
            organism = parts[1].strip(',')
            organism = self._normalize_name(organism)

            #get a list of the uniprot ids, filter out comments and such by matching to the potential ones
            uniprot_id_list = re.split(',|and', parts[4].replace(' ', '').replace(';', '').replace('-', ''))
            uniprot_id_list = [s for s in uniprot_id_list if s in potential and s != u'']

            if uniprot_id_list == ['']:
                return None
            else:
                #print(temperature, organism, uniprot_id_list)
                return organism, uniprot_id_list
        else:
            return None


    def _split_divs(self, divs):
        '''
        Take the organism html section and parse out all divs.

        '''
        all_data = {}
        for div in divs:

            #parse the div
            result = self._parse_single_div(div)
            if result is None:
                continue

            #get the data and process the temperature as an average (if a range is given) and convert to float
            organism, uniprot_id_list = result

            #add to data structure
            if all_data.get(organism) is None:
                all_data[organism] = []

            for uniprot_id in uniprot_id_list:
                all_data[organism].append(uniprot_id)

        return all_data


    def get_data(self):
        '''
        Extract the section of the HTML code that corresponds to the organisms.
        This is from the ORGANISM table in BRENDA.
        '''
        if self.grey1_data == None and self.grey2_data == None and self.hiddengrey1_data == None and self.hiddengrey2_data == None:
            return None

        else:
            #combine the two datasets
            found_at_least_one_uniprot_id = False
            combined_data = {}
            for data in [self.grey1_data, self.grey2_data, self.hiddengrey1_data, self.hiddengrey2_data]:
                for organism in data.keys():
                    if data[organism] != []:

                        if combined_data.get(organism) is None:
                            combined_data[organism] = []
                        found_at_least_one_uniprot_id = True
                        combined_data[organism].extend(data[organism])

            if found_at_least_one_uniprot_id is True:
                return combined_data
            else:
                return None



### three-level divs ###


class TemperatureOptimum(_ThreeLevelDiv):
    '''
    Parsing the TEMPERATURE OPTIMUM table in BRENDA.
    '''
    def __init__(self, soup_instance):
        _ThreeLevelDiv.__init__(self, soup_instance, numeric=True)

        self.table_name = 'TEMPERATURE OPTIMUM'
        self.table_id = 'tab41'
        self._parse()


class Cofactor(_ThreeLevelDiv):
    '''
    Parsing the COFACTOR table in BRENDA.
    '''
    def __init__(self, soup_instance):
        _ThreeLevelDiv.__init__(self, soup_instance, numeric=False)

        self.table_name = 'COFACTOR'
        self.table_id = 'tab48'
        self._parse()


class MetalsAndIons(_ThreeLevelDiv):
    '''
    Parsing the METALS and IONS table in BRENDA.
    '''
    def __init__(self, soup_instance):
        _ThreeLevelDiv.__init__(self, soup_instance, numeric=False)

        self.table_name = 'METALS and IONS'
        self.table_id = 'tab15'
        self._parse()


class Inhibitors(_ThreeLevelDiv):
    '''
    Parsing the INHIBITORS table in BRENDA.
    '''
    def __init__(self, soup_instance):
        _ThreeLevelDiv.__init__(self, soup_instance, numeric=False)

        self.table_name = 'INHIBITORS'
        self.table_id = 'tab11'
        self._parse()


class ActivatingCompound(_ThreeLevelDiv):
    '''
    Parsing the ACTIVATING COMPOUND table in BRENDA.
    '''
    def __init__(self, soup_instance):
        _ThreeLevelDiv.__init__(self, soup_instance, numeric=False)

        self.table_name = 'ACTIVATING COMPOUND'
        self.table_id = 'tab1'
        self._parse()


class SpecificActivity(_ThreeLevelDiv):
    '''
    Parsing the SPECIFIC ACTIVITY table in BRENDA.
    '''
    def __init__(self, soup_instance):
        _ThreeLevelDiv.__init__(self, soup_instance, numeric=True)

        self.table_name = 'SPECIFIC ACTIVITY [µmol/min/mg] '
        self.table_id = 'tab34'
        self._parse()


class PhOptimum(_ThreeLevelDiv):
    '''
    Parsing the pH OPTIMUM table in BRENDA.
    '''
    def __init__(self, soup_instance):
        _ThreeLevelDiv.__init__(self, soup_instance, numeric=True)

        self.table_name = 'pH OPTIMUM'
        self.table_id = 'tab45'
        self._parse()


class PhRange(_ThreeLevelDiv):
    '''
    Parsing the pH RANGE table in BRENDA.
    '''
    def __init__(self, soup_instance):
        _ThreeLevelDiv.__init__(self, soup_instance, numeric=True)

        self.table_name = 'pH RANGE'
        self.table_id = 'tab46'
        self._parse()


class TemperatureRange(_ThreeLevelDiv):
    '''
    Parsing the TEMPERATURE RANGE table in BRENDA.
    '''
    def __init__(self, soup_instance):
        _ThreeLevelDiv.__init__(self, soup_instance, numeric=True)

        self.table_name = 'TEMPERATURE RANGE'
        self.table_id = 'tab42'
        self._parse()


class PhStability(_ThreeLevelDiv):
    '''
    Parsing the pH STABILITY table in BRENDA.
    '''
    def __init__(self, soup_instance):
        _ThreeLevelDiv.__init__(self, soup_instance, numeric=True)

        self.table_name = 'pH STABILITY'
        self.table_id = 'tab47'
        self._parse()


class TemperatureStability(_ThreeLevelDiv):
    '''
    Parsing the TEMPERATURE STABILITY table in BRENDA.
    '''
    def __init__(self, soup_instance):
        _ThreeLevelDiv.__init__(self, soup_instance, numeric=True)

        self.table_name = 'TEMPERATURE STABILITY'
        self.table_id = 'tab43'
        self._parse()




### four-level divs ###


class Km(_FourLevelDiv):
    '''
    Parsing the KM VALUE [mM] table in BRENDA.
    '''
    def __init__(self, soup_instance):
        _FourLevelDiv.__init__(self, soup_instance, numeric=True)

        self.table_name = 'KM VALUE [mM]'
        self.table_id = 'tab12'
        self._parse()


class Kcat(_FourLevelDiv):
    '''
    Parsing the TURNOVER NUMBER [1/s] table in BRENDA.
    '''
    def __init__(self, soup_instance):
        _FourLevelDiv.__init__(self, soup_instance, numeric=True)

        self.table_name = 'TURNOVER NUMBER [1/s]'
        self.table_id = 'tab44'
        self._parse()


class KcatDivKm(_FourLevelDiv):
    '''
    Parsing the TURNOVER NUMBER [1/s] table in BRENDA.
    '''
    def __init__(self, soup_instance):
        _FourLevelDiv.__init__(self, soup_instance, numeric=True)

        self.table_name = 'kcat/KM VALUE [1/mMs-1] '
        self.table_id = 'tab305'
        self._parse()






### five-level divs ###
# SUBSTRATE
# NATURAL SUBSTRATES
# Ki VALUE [mM]
# PDB

### other ###

#
#
#
# si = open_ec('/data/Work/projects/sampling-1-1-3-n/data/raw_external/BRENDA_html/html_data/1.1.1.3.html')
# x = Cofactor(si)
# data = x.get_data()
# print(data)



#
#
#
# def get_data():
#     mycmd = "wget 'http://brenda-enzymes.org/all_enzymes.php' -U 'Mozilla/5.0 (X11; Linux x86_64; rv:30.0) Gecko/20100101 Firefox/30.0' --referer='http://brenda-enzymes.org' -O %s --no-clobber" % (join(RAW_FOLDER, 'all_enzymes.php.html'))
#     os.system(mycmd)
#
#
#     #open the list of EC numbers and find all
#     filepath = join(RAW_FOLDER, 'all_enzymes.php.html')
#     with open(filepath, 'r') as f:
#         data = f.read()
#
#     all_ec = set(re.findall('[0-9]+\.[0-9]+\.[0-9]+\.[0-9a-zA-Z]+', data))
#
#     total = len(list(all_ec))
#     print('Number of EC: %s' % total)
#
#     #process each of these
#     counter = 0
#     for ec in sorted(list(all_ec)):
#
#         if counter % 500 == 0:
#             print('%s of %s processed' % (counter, total))
#         counter +=1
#
#         # Skip files that exist
#         if isfile(join(RAW_FOLDER, 'sequences', '%s.csv' % ec)):
#             if os.path.getsize(join(RAW_FOLDER, 'sequences', '%s.csv' % ec)) > 2:
#                 continue
#         # elif isfile(join(RAW_FOLDER, 'sequences', '%s.fasta' % ec)):
#         #     continue
#
#         ##download html file if it does not exist
#         mycmd = "wget 'http://brenda-enzymes.org/enzyme.php?ecno=%s' -U 'Mozilla/5.0 (X11; Linux x86_64; rv:30.0) Gecko/20100101 Firefox/30.0' --referer='https://www.brenda-enzymes.org/ecexplorer.php?browser=1&f[nodes]=21,1&f[action]=open&f[change]=22' -O %s " % (ec, join(RAW_FOLDER, 'html', '%s.html' % ec))
#         os.system(mycmd)
#
#         #download sequences for ec number, if the file does not exist
#         mycmd = "wget 'https://www.brenda-enzymes.org/sequences.php?download=allcsv&ec=%s' -U 'Mozilla/5.0 (X11; Linux x86_64; rv:30.0) Gecko/20100101 Firefox/30.0' --referer='https://www.brenda-enzymes.org/ecexplorer.php?browser=1&f[nodes]=21,1&f[action]=open&f[change]=22' -O %s " % (ec, join(RAW_FOLDER, 'sequences', '%s.csv' % ec))
#         os.system(mycmd)
#
#         time.sleep(1)
#
#
# def make_fasta():
#     '''Convert BENDA csv file to FASTA'''
#
#     counter = 0
#     files = os.listdir(join(RAW_FOLDER, 'sequences'))
#     for fi in files:
#
#         # skip non-csv files
#         if not fi.endswith('.csv'):
#             continue
#
#         if counter % 500 == 0:
#             print('%s processed' % (counter))
#         counter +=1
#
#         infile = join(RAW_FOLDER, 'sequences', fi)
#         outfile = join(RAW_FOLDER, 'sequences', fi.replace('.csv', '.fasta'))
#
#         # skip files that have been converted
#         if isfile(outfile):
#             if os.path.getsize(outfile) > 2:
#                 continue
#
#         with open(infile, 'r' ,encoding='ISO-8859-1') as f:
#             firstline = f.readline()
#
#             #there are four types of document formats expected
#             if firstline.strip() == '<!DOCTYPE html>':
#                 # make file but keep it empty
#                 with open(outfile, 'w') as fo:
#                     fo.write('\n')
#                 continue
#
#             elif len(firstline.split('\t')) == 7 and len(firstline.split('\t')[2].split('.')) == 4:
#                 line = firstline
#
#             elif firstline.strip() == '#This file is tab stop separated':
#                 header_line = f.readline() # get rid of header
#
#                 # make sure header is ok. I.e. skip files where the third line is not the header
#                 if not header_line.startswith('Accession_Code'):
#                     print(fi)
#                     print(header_line)
#                 line = f.readline()
#
#             elif firstline.startswith('Accession_Code'):
#                 line = f.readline()
#
#             else:
#                 print(fi)
#                 print(firstline)
#                 continue
#
#             with open(outfile, 'w', encoding='utf-8') as fo:
#                 #write data to fasta file
#                 header = ';'.join(line.split('\t')[:-1])
#                 seq = line.split('\t')[-1].strip()
#                 fo.write('>%s\n%s\n' % (header, seq))
#                 lastline = line
#
#                 for line in f:
#                     line = line.encode('utf-8', 'xmlcharrefreplace').decode('utf-8')
#
#                     #skip lines that are exactly the same (there seems to be some duplications)
#                     if lastline == line:
#                         continue
#
#                     #write data to fasta file
#                     header = ';'.join(line.split('\t')[:-1])
#                     seq = line.split('\t')[-1].strip()
#                     fo.write('>%s\n%s\n' % (header, seq))
#                     lastline = line
#
# def compress_data():
#     # compress all .html files, remove the uncompressed ones
#     mycmd = "zip -jm %s %s" % (join(RAW_FOLDER, 'html', 'html_data.zip'), join(RAW_FOLDER, 'html', '*'))
#     os.system(mycmd)
#
#     # compress all .csv files, remove uncompressed ones
#     mycmd = "zip -jm %s %s" % (join(RAW_FOLDER, 'sequences', 'sequence_data_csv.zip'), join(RAW_FOLDER, 'sequences', '*.csv'))
#     os.system(mycmd)
#
#     # compress all .fasta files, remove the uncompressed ones
#     mycmd = "zip -jm %s %s" % (join(RAW_FOLDER, 'sequences', 'sequence_data.zip'), join(RAW_FOLDER, 'sequences', '*.fasta'))
#     os.system(mycmd)
#








#
# def get_all_orgs(self):
#     '''
#     Get all organism data from BRENDA
#     '''
#
#     #open the list of EC numbers and find all
#     filepath = join(RAW_FOLDER, 'all_enzymes.php.html')
#     with open(filepath, 'r') as f:
#         data = f.read()
#     all_ec = set(re.findall('[0-9]+\.[0-9]+\.[0-9]+\.[0-9a-zA-Z]+', data))
#
#     total = len(list(all_ec))
#     print('Number of EC: %s' % total)
#
#     #process each of these
#     data = {}
#     counter = 0
#     for ec in sorted(list(all_ec)):
#         if ec.startswith('1.1.1'):
#             print(ec)
#             counter +=1
#             if counter % 1000 == 0:
#                 print('%s of %s processed' % (counter, total))
#             div_data = get_organism_divs_from_data(ec)
#             #if div_data is not None:
#             data[ec] = div_data
#
#
#     #count how many
#     with open('test.tsv', 'w') as f:
#         f.write('ec\tuniprot_identifiers\n')
#
#         all_uid = []
#         for ec in sorted(data.keys()):
#             ec_uids = []
#
#             if data[ec] is None:
#                 f.write('%s\t%s\n' % (ec, 0))
#             else:
#                 for org in data[ec].keys():
#                     if data[ec][org] is not None:
#                         all_uid.extend(data[ec][org])
#
#                         ec_uids.extend(data[ec][org])
#                 f.write('%s\t%s\n' % (ec, len(set(ec_uids))))
#         print(len(set(all_uid)))
#
#
#
# def get_all_uniprot_id():
#     '''
#     Use regex to get all the uniprot identifiers.
#     Intended as an alternate method that does not depend on parsing the html.
#     '''
#
#     #open the list of EC numbers and find all
#     filepath = join(RAW_FOLDER, 'all_enzymes.php.html')
#     with open(filepath, 'r') as f:
#         data = f.read()
#     all_ec = set(re.findall('[0-9]+\.[0-9]+\.[0-9]+\.[0-9a-zA-Z]+', data))
#
#     total = len(list(all_ec))
#     print('Number of EC: %s' % total)
#
#     #process each of these
#     data = {}
#     counter = 0
#     for ec in sorted(list(all_ec)):
#         #if ec.startswith('1.1.3'):
#         print(ec)
#         html_doc = join(RAW_FOLDER, '%s.html' % ec)
#
#         #read the html page
#         with open(html_doc, 'r') as f:
#             document = f.read()
#
#         #http://www.uniprot.org/help/accession_numbers
#         m = re.findall('>([OPQ][0-9](?:[A-Z0-9]){3}[0-9])<|>([A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})<', document)
#         data[ec] = m
#
#     #count how many
#     with open('test.tsv', 'w') as f:
#         f.write('ec\tuniprot_identifiers\n')
#
#         all_uid = []
#         for ec in sorted(data.keys()):
#             if data[ec] == []:
#                 f.write('%s\t%s\n' % (ec, 0))
#             else:
#                 all_uid.extend(data[ec])
#                 f.write('%s\t%s\n' % (ec, len(set(data[ec]))))
#     print(len(set(all_uid)))
#
#
# get_all_uniprot_id()
#
#
# def get_all(folder_path, table_class):
#     '''Get all temperature data from BRENDA'''
#
#     #open the list of EC numbers and find all
#     filepath = join(folder_path, 'all_enzymes.php.html')
#     with open(filepath, 'r') as f:
#         data = f.read()
#     all_ec = set(re.findall('[0-9]+\.[0-9]+\.[0-9]+\.[0-9a-zA-Z]+', data))
#
#     total = len(list(all_ec))
#     print('Number of EC: %s' % total)
#
#     #process each of these
#     data = {}
#     counter = 0
#     for ec in list(all_ec):
#         counter +=1
#         if counter % 1000 == 0:
#             print('%s of %s processed' % (counter, total))
#
#         soup = open_ec(filepath)
#
#         brenda_obj = table_class(soup)
#
#         data[ec] = brenda_obj.get_data()
#
#     return data
    #
    # #save as shelve
    # sh = shelve.open(join(FINAL_FOLDER, '1_temperature_optimum_data.db'))
    # sh['data'] = data
    # sh.close()
#
#
# def make_flatfile():
#     '''Make a tab-delimited flatfile of data'''
#     sh = shelve.open(join(FINAL_FOLDER, '1_temperature_optimum_data.db'))
#     data = sh['data']
#     sh.close()
#
#     with open(join(FINAL_FOLDER, '1_temperature_optimum_data.tsv'), 'w') as f:
#         f.write('ec\torganism\ttemperature\tuniprot_id\n')
#         for ec in sorted(data.keys()):
#             if data[ec] is None:
#                 continue
#             for org in sorted(data[ec]):
#                 for uniprot_id in sorted(data[ec][org]):
#                     temps = data[ec][org][uniprot_id]
#                     temperature = int(round(sum(temps)/len(temps)))
#                     f.write('%s\t%s\t%s\t%s\n' % (ec, org.lower().replace(' ', '_'), temperature, uniprot_id))
#
#
#
# def get_sequences():
#     '''For each uniprot_id, get the sequence'''
#     sh = shelve.open(join(FINAL_FOLDER, '1_temperature_optimum_data.db'))
#     data = sh['data']
#     sh.close()
#
#     for ec in sorted(data.keys()):
#         if data[ec] is None:
#             continue
#         for org in sorted(data[ec]):
#             for uniprot_id in sorted(data[ec][org]):
#                 url = 'http://www.uniprot.org/uniprot/%s.fasta' % uniprot_id
#                 dlfile(folder=join(DATA_BASE_FOLDER, 'raw_external/', 'uniprot_records'), filename='%s.fasta' % uniprot_id, url=url)
#
#
#
# def make_fasta_files():
#     '''Combine uniprot records into fasta files. Annotate with temperature'''
#     sh = shelve.open(join(FINAL_FOLDER, '1_temperature_optimum_data.db'))
#     data = sh['data']
#     sh.close()
#
#     orgs_in_training_set = []
#     all_orgs = []
#
#     #for each record in folder
#     folder=join(DATA_BASE_FOLDER, 'raw_external/', 'uniprot_records')
#     all_files = os.listdir(folder)
#     for fi in sorted(all_files):
#         with open(join(folder, fi), 'r') as f:
#             header = f.readline()
#             seq = f.read()
#             uniprot_id = fi.replace('.fasta', '')
#
#             #parse out orgname
#             org = re.search('OS=[\[\]a-zA-Z]+\s[a-zA-Z]+', header).group(0)
#             org = org.replace('OS=', '').replace('[', '').replace(']', '')
#
#             #pair with its measured temperature
#             for ec in data.keys():
#                 if data[ec] is None:
#                     continue
#                 if data[ec].get(org, {}).get(uniprot_id) is not None:
#                     temps = data[ec][org][uniprot_id]
#                     temperature = int(round(sum(temps)/len(temps)))
#                     break
#
#             #craft the output
#             out_record = '>%s;%s\n%s' % (org, temperature, seq)
#
#             #check whether this organism is in my growth data
#             if org_temp_new.in_data(org) is True:
#                 #make one fasta file with organisms that were in my dataset
#                 orgs_in_training_set.append(out_record)
#
#             #make one fasta file with all records
#             all_orgs.append(out_record)
#
#
#     with open(join(FINAL_FOLDER, 'orgs_in_training_set.fasta'), 'w') as f:
#         f.write('\n'.join(orgs_in_training_set))
#
#     with open(join(FINAL_FOLDER, 'all_orgs.fasta'), 'w') as f:
#         f.write('\n'.join(all_orgs))


#get_all()
#make_flatfile()
#get_sequences()
#make_fasta_files()
