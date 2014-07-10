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
        self.alpha = alpha

        url = "sci="+self.genus+"%20"+self.species+"&back=30&maxResults=1&includeProvisional=true"
        self.url = url

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

usa = "http://ebird.org/ws1.1/data/obs/region_spp/recent?rtype=country&r=US&"
canada = "http://ebird.org/ws1.1/data/obs/region_spp/recent?rtype=country&r=CA&"

#FLASK FRAMEWORK
app = Flask(__name__)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/attribution")
def attribution():
    return render_template("attribution.html")

@app.route("/select", methods=["POST"])
def select():
    #SENDS SPECIES-SPECIFIC REQUEST TO EBIRD FOR US AND CANADA REGIONS
    for bird in bird_list:
        if bird.alpha == str(request.form["OWL"]):
            species_alpha = bird.alpha
            species_name = bird.name
            species_sci = (str(bird.genus[0])).upper()+str(bird.genus[1:])+" "+str(bird.species)
            species_url = bird.url           
    usa_xml = requests.get(usa+species_url)
    canada_xml = requests.get(canada+species_url)
    #PARSES XML AND DETERMINES WHICH OF US OR CANADA HAS THE MOST RECENT OBSERVATION
    usa_parsed = minidom.parseString(usa_xml.content)
    canada_parsed = minidom.parseString(canada_xml.content)
    usa_raw_date = usa_parsed.getElementsByTagName('obs-dt')
    canada_raw_date = canada_parsed.getElementsByTagName('obs-dt')   
    if (len(usa_raw_date) == 0) and (len(canada_raw_date) == 0):
        return render_template("not_found.html", species_name = species_name, species_alpha = species_alpha)
    elif (len(usa_raw_date) != 0) and (len(canada_raw_date) != 0):
        usa_date = datetime.datetime.strptime(usa_raw_date[-1].childNodes[0].nodeValue, '%Y-%m-%d %H:%M')   
        canada_date = datetime.datetime.strptime(canada_raw_date[-1].childNodes[0].nodeValue, '%Y-%m-%d %H:%M')
        most_recent = max(usa_date, canada_date)
        if most_recent == usa_date:
            observation = ET.fromstring(usa_xml.content)
        elif most_recent == canada_date:
            observation = ET.fromstring(canada_xml.content)
    elif (len(usa_raw_date) != 0) and (len(canada_raw_date) == 0):
        most_recent = datetime.datetime.strptime(usa_raw_date[-1].childNodes[0].nodeValue, '%Y-%m-%d %H:%M') 
        observation = ET.fromstring(usa_xml.content)
    elif (len(usa_raw_date) == 0) and (len(canada_raw_date) != 0):
        most_recent = datetime.datetime.strptime(canada_raw_date[-1].childNodes[0].nodeValue, '%Y-%m-%d %H:%M') 
        observation = ET.fromstring(canada_xml.content)
    #FORMATS RESULTS FOR DISPLAY AND RENDERS TO TEMPLATE
    location_name = ((observation.findall("./result/sighting/loc-name"))[-1])
    latitude = ((observation.findall("./result/sighting/lat"))[-1])
    latitude = latitude.text
    longitude = ((observation.findall("./result/sighting/lng"))[-1])
    longitude = longitude.text
    date = str(most_recent.strftime('%A, %Y-%m-%d'))
    location = location_name.text+" ("+latitude+", "+longitude+")"
    return render_template("result.html", location = location, latitude = latitude, longitude = longitude, date = date, species_alpha = species_alpha, species_name = species_name, species_sci = species_sci)


if __name__ == "__main__":
    app.run(debug=True)

