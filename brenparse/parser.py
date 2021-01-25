#!/usr/bin/env python3


import sys
if sys.version_info[0] != 3:
    sys.exit("Sorry, only Python 3 is supported by this script.")

import os
from os.path import join, exists
from bs4 import BeautifulSoup
import re
from pkg_resources import resource_stream

EXAMPLE_PAGE = resource_stream(__name__, 'data/1.1.3.15.html').name

def open_ec(filepath):
    '''
    Open the EC html file that should be parsed.
    Return a soup instance.
    '''
    with open(filepath, 'r', encoding='ISO-8859-1') as f:
        soup = BeautifulSoup(f, 'html.parser')
    return soup


def get_identifiers_from_html(my_string):
    '''
    Alternate way to get all identifiers.
    http://www.uniprot.org/help/accession_numbers
    '''
    return re.findall('([OPQ][0-9](?:[A-Z0-9]){3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})', my_string)



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
        organism = ' '.join(organism.split()[:2]).rstrip(',.')

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
    The expected structure is "value, organism, uniprot_id"
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
            potential.append(item.get_text().upper())
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
            uniprot_id_list = get_identifiers_from_html(parts[3].upper())
            uniprot_id_list = [s for s in uniprot_id_list if s in potential or get_identifiers_from_html(s) != []]

            if uniprot_id_list == [''] or uniprot_id_list == []: # if uid is unknown
                return value, organism, ['unknown']
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


    def get_data(self, uid_orgs_only=True):
        '''
        Extract the section of the HTML code that corresponds to the desired table.
        Then parse it and combine all the data.
        '''
        found_at_least_one_uniprot_id = not uid_orgs_only

        if self.grey1_data == None and self.grey2_data == None and self.hiddengrey1_data == None and self.hiddengrey2_data == None:
            return None

        else:
            #combine the two datasets
            combined_data = {}
            for data in [self.grey1_data, self.grey2_data, self.hiddengrey1_data, self.hiddengrey2_data]:
                for organism in data.keys():

                    #if (uid_orgs_only is True and data[organism] != []) or (uid_orgs_only is False):

                    if data[organism] != {}:
                        for uniprot_id in data[organism].keys():

                            if uniprot_id == 'unknown' and uid_orgs_only: # skip data not connected to a uid, if desired
                                continue

                            found_at_least_one_uniprot_id = True

                            if combined_data.get(organism) is None:
                                combined_data[organism] = {}

                            if combined_data[organism].get(uniprot_id) is None:
                                combined_data[organism][uniprot_id] = []

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
    The expected structure is "value, information, organism, uniprot_id"
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
            potential.append(item.get_text().upper())
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
            uniprot_id_list = get_identifiers_from_html(parts[4].upper())
            uniprot_id_list = [s for s in uniprot_id_list if s in potential or get_identifiers_from_html(s) != []]
            #print(uniprot_id_list)

            if uniprot_id_list == [''] or uniprot_id_list == []: # if uid is unknown
                return value, information, organism, ['unknown']
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


    def get_data(self, uid_orgs_only=True):
        '''
        Extract the section of the HTML code that corresponds to the value
        '''
        found_at_least_one_uniprot_id = not uid_orgs_only

        if self.grey1_data == None and self.grey2_data == None and self.hiddengrey1_data == None and self.hiddengrey2_data == None:
            return None

        else:
            #combine the two datasets
            combined_data = {}
            for data in [self.grey1_data, self.grey2_data, self.hiddengrey1_data, self.hiddengrey2_data]:
                for organism in data.keys():

                    if data[organism] != {}:
                        for uniprot_id in data[organism].keys():

                            if uniprot_id == 'unknown' and uid_orgs_only: # skip data not connected to a uid, if desired
                                continue

                            found_at_least_one_uniprot_id = True

                            if combined_data.get(organism) is None:
                                combined_data[organism] = {}

                            if combined_data[organism].get(uniprot_id) is None:
                                combined_data[organism][uniprot_id] = {}

                            for information in data[organism][uniprot_id].keys():
                                if combined_data[organism][uniprot_id].get(information) is None:
                                    combined_data[organism][uniprot_id][information] = []

                                combined_data[organism][uniprot_id][information].extend(data[organism][uniprot_id][information])

            if found_at_least_one_uniprot_id is True:
                return combined_data
            else:
                return None




class _FiveLevelDiv(_BrendaBaseClass):
    '''
    The divs have different "depths", different number of cells before I get to the UNIPROT ID.
    This class can parse divs that has a depth of five.
    "numeric" determines whether the first value in the table is expected to be numeric or not.
    The expected structure is "value1, value2, information, organism, uniprot_id"
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
            potential.append(item.get_text().upper())
        potential = list(filter(None, potential))

        #get all div text
        text = div.get_text(',')
        if len(text.split('\n')) > 3:
            parts = text.split('\n')

            # first one tends to be empty
            if parts[0] == '':
                parts = parts[1:]

            # get rid of comma
            parts = [s.strip(',') for s in parts]

            #get substrates and products
            substrates = parts[0].split(' + ')
            products = parts[1].split(' + ')

            if substrates == ['additional information']:
                return None

            if products == ['additional information']:
                return None

            # get the info cell
            information = parts[2].strip(',')

            #get organism
            organism = parts[3].strip(',')
            organism = self._normalize_name(organism)

            #get a list of the uniprot ids, filter out comments and such by matching to the potential ones
            uniprot_id_list = get_identifiers_from_html(parts[4].upper())
            uniprot_id_list = [s for s in uniprot_id_list if s in potential or get_identifiers_from_html(s) != []]

            if uniprot_id_list == [''] or uniprot_id_list == []: # if uid is unknown
                return substrates, products, organism, ['unknown']
            else:
                return substrates, products, organism, uniprot_id_list
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

            substrates, products, organism, uniprot_id_list = result

            #add to data structure
            if all_data.get(organism) is None:
                all_data[organism] = {}

            for uniprot_id in uniprot_id_list:
                if all_data[organism].get(uniprot_id) is None:
                    all_data[organism][uniprot_id] = []

                all_data[organism][uniprot_id].append({'sub':substrates, 'prod':products})

        return all_data


    def get_data(self, uid_orgs_only=True):
        '''
        Extract the section of the HTML code that corresponds to the value
        '''
        found_at_least_one_uniprot_id = not uid_orgs_only

        if self.grey1_data == None and self.grey2_data == None and self.hiddengrey1_data == None and self.hiddengrey2_data == None:
            return None

        else:
            #combine the two datasets
            combined_data = {}
            for data in [self.grey1_data, self.grey2_data, self.hiddengrey1_data, self.hiddengrey2_data]:
                for organism in data.keys():

                    if data[organism] != {}:
                        for uniprot_id in data[organism].keys():

                            if uniprot_id == 'unknown' and uid_orgs_only: # skip data not connected to a uid, if desired
                                continue

                            found_at_least_one_uniprot_id = True

                            if combined_data.get(organism) is None:
                                combined_data[organism] = {}

                            if combined_data[organism].get(uniprot_id) is None:
                                combined_data[organism][uniprot_id] = []

                            combined_data[organism][uniprot_id].extend(data[organism][uniprot_id])

            if found_at_least_one_uniprot_id is True:
                return combined_data
            else:
                return None



class Organism(_BrendaBaseClass):
    '''
    Parsing the ORGANISM table in BRENDA.
    It's a special case as it has no data values, so I don't use subclassing of the other LevelDiv classes.
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
            potential.append(item.get_text().upper())
        potential = list(filter(None, potential))

        #get all div text
        text = div.get_text(',')
        if len(text.split('\n')) > 3:
            parts = text.split('\n')


            #get organism
            organism = parts[1].strip('.,')
            if organism.lower().strip().startswith('no activity'): # sometimes the organism field says, no activity in ... , get rid of this
                return None

            organism = self._normalize_name(organism)

            #get a list of the uniprot ids, filter out comments and such by matching to the potential ones
            uniprot_id_list = get_identifiers_from_html(parts[4].upper())
            uniprot_id_list = [s for s in uniprot_id_list if (s in potential or get_identifiers_from_html(s) != []) and s != u'']

            if uniprot_id_list == ['']: # if uid is unknown
                return organism, []
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
                all_data[organism] = set([])

            for uniprot_id in uniprot_id_list:
                all_data[organism].add(uniprot_id)

        return all_data


    def get_data(self, uid_orgs_only=True):
        '''
        Extract the section of the HTML code that corresponds to the organisms.
        This is from the ORGANISM table in BRENDA.
        '''
        found_at_least_one_uniprot_id = not uid_orgs_only

        if self.grey1_data == None and self.grey2_data == None and self.hiddengrey1_data == None and self.hiddengrey2_data == None:
            return None

        else:
            #combine the two datasets
            combined_data = {}
            for data in [self.grey1_data, self.grey2_data, self.hiddengrey1_data, self.hiddengrey2_data]:
                for organism in data.keys():
                    if (uid_orgs_only is True and data[organism] != set([])) or (uid_orgs_only is False):

                        if combined_data.get(organism) is None:
                            combined_data[organism] = set([])

                        found_at_least_one_uniprot_id = True
                        combined_data[organism] = combined_data[organism] | data[organism]

            if found_at_least_one_uniprot_id is True:
                for key in combined_data.keys(): # convert to sorted list
                    combined_data[key] = sorted(list(combined_data[key]))
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
    Parsing the kcat/KM VALUE [1/mMs-1] table in BRENDA.
    '''
    def __init__(self, soup_instance):
        _FourLevelDiv.__init__(self, soup_instance, numeric=True)

        self.table_name = 'kcat/KM VALUE [1/mMs-1] '
        self.table_id = 'tab305'
        self._parse()






### five-level divs ###

class Substrate(_FiveLevelDiv):
    '''
    Parsing the SUBSTRATE table in BRENDA.
    '''
    def __init__(self, soup_instance):
        _FiveLevelDiv.__init__(self, soup_instance, numeric=False)

        self.table_name = 'SUBSTRATE'
        self.table_id = 'tab37'
        self._parse()


class NaturalSubstrate(_FiveLevelDiv):
    '''
    Parsing the NATURAL SUBSTRATE table in BRENDA.
    '''
    def __init__(self, soup_instance):
        _FiveLevelDiv.__init__(self, soup_instance, numeric=False)

        self.table_name = 'NATURAL SUBSTRATE'
        self.table_id = 'tab17'
        self._parse()


# Ki VALUE [mM]
# PDB

### other ###

