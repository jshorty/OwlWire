from xml.dom import minidom
from flask import Flask, render_template, request, Markup
import xml.etree.ElementTree as ET
import requests
import datetime

class Bird(object):
    def __init__(self, name, genus, species, alpha):
        self.name = name
        self.genus = genus
        self.species = species
        self.alpha = alpha #4-LETTER ALPHA CODE
        #URL INFORMATION SPECIFIC TO THE EBIRD API, FOR REPORTS OF A SINGLE SPECIES IN A COUNTRY
        ebird_url = "sci="+self.genus+"%20"+self.species+"&back=30&maxResults=1&includeProvisional=true"
        self.ebird_url = ebird_url

#DATA FOR OWLS FOUND IN NORTH AMERICA, INLINE HERE FOR CONVENIENCE
BDOW = Bird("Barred Owl", "strix", "varia", "BDOW")
BNOW = Bird("Barn Owl", "tyto", "alba", "BNOW")
BOOW = Bird("Boreal Owl", "aegolius", "funereus", "BOOW")
BUOW = Bird("Burrowing Owl", "athene", "cunicularia", "BUOW")
ESOW = Bird("Eastern Screech-Owl", "megascops", "asio", "ESOW")
ELOW = Bird("Elf Owl", "micrathene", "whitneyi", "ELOW")
FPOW = Bird("Ferruginous Pygmy-Owl", "glaucidium", "brasilianum", "FPOW")
FLOW = Bird("Flammulated Owl", "psiloscops", "flammeolus", "FLOW")
GGOW = Bird("Great Gray Owl", "strix", "nebulosa", "GGOW")
GHOW = Bird("Great Horned Owl", "bubo", "virginianus", "GHOW")
LEOW = Bird("Long-eared Owl", "asio", "otus", "LEOW")
NHOW = Bird("Northern Hawk Owl", "surnia", "ulula", "NHOW")
NPOW = Bird("Northern Pygmy-Owl", "glaucidium", "gnoma", "NPOW")
NSWO = Bird("Northern Saw-whet Owl", "aegolius", "acadicus", "NSWO")
SEOW = Bird("Short-eared Owl", "asio", "flammeus", "SEOW")
SNOW = Bird("Snowy Owl", "bubo", "scandiacus", "SNOW")
SPOW = Bird("Spotted Owl", "strix", "occidentalis", "SPOW")
WESO = Bird("Western Screech-Owl", "megascops", "kennicottii", "WESO")
WHSO = Bird("Whiskered Screech-Owl", "megascops", "trichopsis", "WHSO")
bird_list = [BDOW, BNOW, BOOW, BUOW, ESOW, ELOW, FPOW, FLOW, GGOW, GHOW, LEOW, NHOW, NPOW, NSWO, SEOW, SNOW, SPOW, WESO, WHSO]
country_list = ["US", "CA"] #TWO-LETTER COUNTRY ABBREVIATIONS USED BY EBIRD

#IDENTIFIES SPECIES SELECTED ON HTML FORM, RETURNS RELEVANT BIRD OBJECT
def id_selected_species():
    for bird in bird_list:
        if bird.alpha == str(request.form["OWL"]):
            return bird

#QUERIES EBIRD API WITH A SPECIES-SPECIFIC URL, RETURNS A DICTIONARY WITH XML FOR EACH QUERIED COUNTRY
def query_ebird(bird, country_list):
    country_raw_xml_dict = {}
    for country_code in country_list:
        retrieved_XML = requests.get("http://ebird.org/ws1.1/data/obs/region_spp/recent?rtype=country&r="+country_code+"&"+bird.ebird_url)
        country_raw_xml_dict[country_code] = retrieved_XML
    return country_raw_xml_dict

#PARSES EACH COUNTRY'S RAW XML FROM ONE DICTIONARY AND PUTS IT INTO ANOTHER
def parse_country_xml(country_raw_xml_dict, country_list):
    country_parsed_xml_dict = {}
    for country_code in country_list:
        parsed_XML = minidom.parseString(country_raw_xml_dict[country_code].content)
        country_parsed_xml_dict[country_code] = parsed_XML
    return country_parsed_xml_dict

#FINDS DATE/TIME OF THE OBSERVATION WITHIN EBIRD API'S RETURNED XML
def find_obs_in_xml(xml_with_obs_dt):
    return xml_with_obs_dt.getElementsByTagName('obs-dt')

#CONVERTS OBSERVATION TO DATETIME OBJECT FOR COMPARISON (TO LATER FIND MOST RECENT)
def convert_obs_to_datetime(observation):
    try:
        converted = datetime.datetime.strptime(observation[-1].childNodes[0].nodeValue, '%Y-%m-%d %H:%M')
    except ValueError: #HANDLES EXCEPTIONS: SOMETIMES OBSERVATION DOES NOT INCLUDE TIME OF DAY
        converted = datetime.datetime.strptime(observation[-1].childNodes[0].nodeValue, '%Y-%m-%d')
    return converted

#TAKES A DICTIONARY OF COUNTRY-SPECIFIC REPORTS AND DETERMINES THE MOST RECENT
def determine_most_recent_obs(country_parsed_xml_dict):
    country_observation_dates = {}
    countries_without_a_report = []
    reports_for_each_country = True
    for country in country_list:
        observation_date = find_obs_in_xml(country_parsed_xml_dict[country])
        if len(observation_date) == 0: #NOTES IF ANY COUNTRY LACKS A REPORT (HAPPENS IF LAST SIGHTING WAS >30 DAYS AGO)
            countries_without_a_report.append(country)
            reports_for_each_country = False
        else:
            country_observation_dates[country] = convert_obs_to_datetime(observation_date)
    if len(countries_without_a_report) == len(country_list): #NOTES IF NO REPORTS FOUND AT ALL
        country_with_most_recent = "No recent observations"
    #DETERMINES MOST RECENT OF ALL OBSERVATIONS
    country_with_most_recent = (max(country_observation_dates.keys(), key=country_observation_dates.get))
    return country_with_most_recent

#CALLING ALL THE FUNCTIONS
def owlwire():
    selected_bird = id_selected_species()
    country_raw_xml_dict = query_ebird(selected_bird, country_list)
    country_parsed_xml_dict = parse_country_xml(country_raw_xml_dict, country_list)
    country_with_most_recent = determine_most_recent_obs(country_parsed_xml_dict)
    return(selected_bird, country_with_most_recent, country_raw_xml_dict, country_parsed_xml_dict)

#FLASK HTML FRAMEWORK
app = Flask(__name__)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/attribution")
def attribution():
    return render_template("attribution.html")

@app.route("/select", methods=["POST"]) #WHAT HAPPENS WHEN YOU CLICK A BIRD ON THE WEBSITE
def select():
    owlwire_tuple = owlwire()
    bird = owlwire_tuple[0]
    country_with_most_recent = owlwire_tuple[1]
    country_raw_xml_dict = owlwire_tuple[2]
    country_parsed_xml_dict= owlwire_tuple[3]
    #IF NO REPORTS FOUND:
    if country_with_most_recent == "No recent observations":
        return render_template("not_found.html", species_name = bird.name, species_alpha = bird.alpha)
    #OTHERWISE: BELOW IS FORMATTING DATA FIELDS FROM THE XML OF THE REPORT FOR PRESENTATION IN HTML THROUGH FLASK
    report_xml = country_raw_xml_dict[country_with_most_recent]
    report_content = ET.fromstring(report_xml.content)
    report_datetime = convert_obs_to_datetime(find_obs_in_xml(country_parsed_xml_dict[country_with_most_recent]))
    location_name = ((report_content.findall("./result/sighting/loc-name"))[-1])
    lat = ((report_content.findall("./result/sighting/lat"))[-1])
    long = ((report_content.findall("./result/sighting/lng"))[-1])
    latitude = lat.text
    longitude = long.text
    location = location_name.text+" ("+latitude+", "+longitude+")"
    date = str(report_datetime.strftime('%A, %Y-%m-%d'))
    species_alpha = bird.alpha
    species_name = bird.name
    species_sci = (str(bird.genus[0])).upper()+str(bird.genus[1:])+" "+str(bird.species)
    species_ebird_url = bird.ebird_url
    return render_template("result.html", location = location, latitude = latitude, longitude = longitude, date = date, species_alpha = species_alpha, species_name = species_name, species_sci = species_sci)
    
if __name__ == "__main__":
    app.run(debug=True)
