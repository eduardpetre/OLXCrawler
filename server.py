from email import message
from flask import Flask, render_template
app = Flask(__name__)

from os import link
from pickletools import string4
from robobrowser import RoboBrowser
from bs4 import BeautifulSoup
from multiprocessing import Pool
import time
import re

currentIteration = [0]
pretComparare = [100, 150, 200, 250, 300, 400, 500, 750, 1000, 1500, 2000, 5000, 10000, 50000, 100000, 200000, 500000, 1000000, 5000000]
anConstructieComparare = [1900, 1925, 1950, 1970, 1980, 1990, 2000, 2010, 2015, 2020, 2022]
suprafataUtilaComparare = [40, 60, 80, 100, 150, 200, 500, 1000, 2000, 5000]
typeFilters = ["Suprafata utila:", "Numarul de camere:", "Tip anunt:", "Obiect de vanzare:", "Tipul de persoana:", "Etaj:", "Anul constructiei:", "Pret:", "Oras:", "Compartimente:"]
globalFilters = [{}, {}, {}, {}, {}, {}, {}, {}, {}, {}]

start = time.time()

lv = []
baseURL = "https://www.olx.ro/imobiliare/?page="

nrpagmax = 0
def find_maxPage():
    return
    browser = RoboBrowser(parser="html5lib")
    browser.open(baseURL)

    htmlpage = str(browser.parsed)
    bsoup = BeautifulSoup(htmlpage, "html5lib")

    pag = bsoup.find_all("a", {"class": "block br3 brc8 large tdnone lheight24"})
    nrpag = pag[-1].find("span")
    nrpagmax = nrpag.text
#nrpagmax sa stiu pe cate pagini sa merg

def generate():
    find_maxPage()
    nrpagmax = 15
    i = 1
    print("Generate link:")
    while i <= int(nrpagmax):
        URL = baseURL + str(i)

        browser = RoboBrowser(parser = "html5lib")
        browser.open(URL)

        htmlpage = str(browser.parsed)
        bsoup = BeautifulSoup(htmlpage, "html5lib")

        anunturi = bsoup.find_all("tr", {"class" : "wrap"})

        for anunt in anunturi:
            for link in anunt.find_all('a'):
                x = link.get('href')
                if x not in lv:
                    lv.append(x)

        print("Last page done:", i)
        i+=1

def scrape_anunt(x):
    localFilters = [{}, {}, {}, {}, {}, {}, {}, {}, {}, {}]
    if (x[:5] == "https"):
        if (str(x[12] + x[13] + x[14]) == "sto"):  # pt anunturile de pe storia
            #print(x)
            anunt = RoboBrowser(parser="html5lib")
            anunt.open(x)

            htmlpage = str(anunt.parsed)
            bsoup = BeautifulSoup(htmlpage, "html5lib")
            header = bsoup.title.text
            #filtru = bsoup.find_all("div", {"class": "css-1ccovha estckra9"}) # filtru + valoarea filtru
            try:
                filtru = bsoup.find("div", {"data-testid": "ad.top-information.table"})
            except:
                print("filtru ", x)
                return localFilters

            try:
                pret = bsoup.find("strong", {"class": "css-8qi9av eu6swcv19"}).text
            except:
                print("pret", x)
                return localFilters

            if bsoup.find("div", {"data-cy": "adPageAdDescription"}):
                descriere = bsoup.find("div", {"data-cy": "adPageAdDescription"}).text
            else:
                descriere = ""
            
            getFiltre("\n".join((str(pret), str(header), str(filtru), str(descriere))), str(x), localFilters)
        else:
            #print(x)
            # pt anunturile de pe olx
            anunt = RoboBrowser(parser="html5lib")
            anunt.open(x)
            htmlpage = str(anunt.parsed)
            bsoup = BeautifulSoup(htmlpage, "html5lib")
            #print(bsoup)
            if bsoup.title:
                header = bsoup.title.text
            else:
                header = ""
            filtre_site = bsoup.find_all("ul", {"class": "css-sfcl1s"})
            pret = bsoup.find("div", {"data-testid": "ad-price-container"}).text
            if bsoup.find("div", {"class": "css-g5mtbi-Text"}):
                descriere = bsoup.find("div", {"class": "css-g5mtbi-Text"}).text
            else:
                descriere = ""

            getFiltre("\n".join((str(pret), str(header), str(filtre_site), str(descriere))), str(x), localFilters)

    currentIteration[0] += 1
    if currentIteration[0] % 10 == 0:
        print("Done with", currentIteration[0] * 10, "announces")

    return localFilters

def newValueString(string):
    string = string.lower()
    newString = ""
    for letter in string:
        if letter == 'ă' or letter == 'â':
            newString += 'a'
        elif letter == 'î':
            newString += 'i'
        elif letter == 'ș':
            newString += 's'
        elif letter == 'ț':
            newString += 't'
        else:
            newString += letter

    return newString

def getFiltre(string, link, localFilters):
    okToPrint = True
    newLine = False
    newString = ""
    for letter in string:
        if letter == '{' or letter == '<':
            okToPrint = False
        elif letter == '}' or letter == '>':
            okToPrint = True
            if newLine == True:
                newLine = False
                #newString += "\n"
        elif okToPrint == True:
            newString += letter
            newLine = True

    filter_1 = "suprafata utila(: |)(\d+|\d+ \d+|\d+ \d+ \d+)(| )m|(\d+|\d+ \d+|\d+ \d+ \d+)(| |-)mp"
    filter_2 = "\d+"
    val = searchInNewString(newString, filter_1, filter_2, "Suprafata utila: ", "Nu este specificata suprafata utila!", link)
    if val != None:
        val = int(val)
        ok = False
        for cmp in suprafataUtilaComparare:
            if val <= cmp:
                localFilters[0][cmp] = localFilters[0].get(cmp, 0) + 1
                ok = True
                break
        if ok == False:
            localFilters[0]["another"] = localFilters[0].get("another", 0) + 1
    else:
        localFilters[0]["none"] = localFilters[0].get("none", 0) + 1

    filter_1 = "\d+(| )camere|camere(:|)(| )\d+"
    filter_2 = "\d+"
    val = searchInNewString(newString, filter_1, filter_2, "Numar de camere: ", "Nu este specificat numarul de camere!", link)
    if val != None:
        val = int(val)
        localFilters[1][val] = localFilters[1].get(val, 0) + 1
    else:
        localFilters[1]["none"] = localFilters[1].get("none", 0) + 1

    filter_1 = "v(a|â)nzare|v(a|â)nd|vinde|cump(a|ă)rare|cump(a|ă)r|(i|î)nchiriere|(i|î)nchiriez|(i|î)nchiriat|achizi(t|ț)ie"
    filter_2 = "\w+"
    tip = searchInNewString(newString, filter_1, filter_2, "Tip de anunt: ", "Nu este specificat tipul de anunt!", link)
    if tip != None:
        tip = newValueString(tip)
        regexFind = re.search("v(a|â)nzare|v(a|â)nd|vinde|achizi(t|ț)ie", tip)
        regexFind = re.search("cump(a|ă)rare|cump(a|ă)r", tip)
        if regexFind != None:
            localFilters[2]["cumparare"] = localFilters[2].get("cumparare", 0) + 1
        else:
            regexFind = re.search("(i|î)nchiriere|(i|î)nchiriez|(i|î)nchiriat", tip)
            if regexFind != None:
                localFilters[2]["inchiriere"] = localFilters[2].get("inchiriere", 0) + 1
            else:
                localFilters[2]["vanzare"] = localFilters[2].get("vanzare", 0) + 1
    else:
        localFilters[2]["vanzare"] = localFilters[2].get("vanzare", 0) + 1

    filter_1 = "teren|apartament|vil(a|ă)|cas(a|ă)|hotel|cabana|spatiu comercial|garsonier(a|ă)"
    filter_2 = "\w+ \w+|\w+"
    val = searchInNewString(newString, filter_1, filter_2, "Obiect de vanzare: ", "Nu este specificat obiectul de vanzare!", link)
    if val != None:
        val = newValueString(val)
        localFilters[3][val] = localFilters[3].get(val, 0) + 1
    else:
        localFilters[3]["another"] = localFilters[3].get("another", 0) + 1

    filter_1 = "persoan(a|ă) fizic(a|ă)|firm(a|ă)"
    filter_2 = "\w+ \w+|\w+"
    val = searchInNewString(newString, filter_1, filter_2, "Tip de persoana: ", "Nu este specificat tipul de persoana!", link)
    if val != None:
        val = newValueString(val)
        localFilters[4][val] = localFilters[4].get(val, 0) + 1
    else:
        localFilters[4]["none"] = localFilters[4].get("none", 0) + 1

    filter_1 = "etaj(|ul)(| |-)(\d+|parter)"
    filter_2 = "(\d+|parter)"
    val = searchInNewString(newString, filter_1, filter_2, "Etaj: ", "Nu este specificat etajul!", link)
    if val != None:
        val = newValueString(val)
        localFilters[5][val] = localFilters[5].get(val, 0) + 1
    else:
        localFilters[5]["none"] = localFilters[5].get("none", 0) + 1

    filter_1 = "(19|20)\d\d(| )[^mp]"
    filter_2 = "\d+"
    val = searchInNewString(newString, filter_1, filter_2, "An constructie: ", "Nu este specificat anul constructiei!", link)
    if val != None:
        val = int(val)
        ok = False
        for cmp in anConstructieComparare:
            if val <= cmp:
                localFilters[6][cmp] = localFilters[6].get(cmp, 0) + 1
                ok = True
                break
        if ok == False:
            localFilters[6]["another"] = localFilters[6].get("another", 0) + 1
    else:
        localFilters[6]["none"] = localFilters[6].get("none", 0) + 1

    filter_1 = "(\d+|\d+(| |.)\d+|\d+(| |.)\d+(| |.)\d+)(| )(euro|lei|€|ron)"
    filter_2 = "(\d+(| |.)\d+(| |.)\d+|\d+(| |.)\d+|\d+)(| )(euro|lei|€|ron)"
    val = searchInNewString(newString, filter_1, filter_2, "Pret: ", "Nu este specificat pretul!", link)
    if val != None:
        val = newValueString(val)
        regexFind = re.search("lei|ron", val)
        if regexFind != None:
            isRon = True
        else: isRon = False
        val = re.search("\d+(| |.)\d+(| |.)\d+|\d+(| |.)\d+|\d+", val)
        newVal = ""
        for letter in val.group():
            if letter == ' ' or letter == '.' or letter == ',':
                continue
            newVal += letter
        val = int(newVal)
        if isRon == True:
            val = val // 5
        ok = False
        for cmp in pretComparare:
            if val <= cmp:
                localFilters[7][cmp] = localFilters[7].get(cmp, 0) + 1
                ok = True
                break
        if ok == False:
            localFilters[7]["another"] = localFilters[7].get("another", 0) + 1
    else:
        localFilters[7]["none"] = localFilters[7].get("none", 0) + 1

    filter_1 = "bucure(s|ș)ti|bra(s|ș)ov|gala(t|ț)i|constan(t|ț)a|sibiu|arad|bac(a|ă)u|craiova|ia(s|ș)i|timi(s|ș)oara|foc(s|ș)ani|roman|cluj|ploie(s|ș)ti|oradea|br(a|ă)ila"
    filter_2 = "\w+"
    val = searchInNewString(newString, filter_1, filter_2, "Oras: ", "Nu este specificat orasul!", link)
    if val != None:
        val = newValueString(val)
        localFilters[8][val] = localFilters[8].get(val, 0) + 1
    else:
        localFilters[8]["another"] = localFilters[8].get("another", 0) + 1

    filter_1 = "decomandat|semidecomandat|circular|nedecomandat"
    filter_2 = "\w+"
    val = searchInNewString(newString, filter_1, filter_2, "Compartimente: ", "Nu este specificat tipul de compartimente!", link)
    if val != None:
        val = newValueString(val)
        localFilters[9][val] = localFilters[9].get(val, 0) + 1
    else:
        localFilters[9]["none"] = localFilters[9].get("none", 0) + 1

def searchInNewString(newString, filter_1, filter_2, wasFoundMessage, wasntFoundMessage, link):
    regexFind = re.search(filter_1, newString, re.IGNORECASE)
    if regexFind != None:
        val = re.search(filter_2, regexFind.group(), re.IGNORECASE)
        val = val.group()
        #print(link, "\n", wasFoundMessage, val, sep="")
        return val
    else:
        #print(link, "\n", wasntFoundMessage, sep="")
        return None

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/filters/')
def main():
    start = time.time()
    generate()
    print("Anunturi", len(lv))
    print("Generate filters:")
    # for x in lv:
    #     scrape_anunt(x)
    p = Pool(10)
    localFilters = p.map(scrape_anunt, lv)
    p.terminate()
    p.join()

    for array in localFilters:
        idx = 0
        if array == None:
            continue
        for dict in array:
            for x in dict.items():
                globalFilters[idx][x[0]] = globalFilters[idx].get(x[0], 0) + x[1]
            idx += 1

    idx = 0
    f = open("templates/getTemplateFilters.txt", "r")
    newString = f.read()
    f.close()
    newString += "<h3> Au fost gasite "  + str(len(lv)) + " anunturi<br>" + "</h3>"
    for dict in globalFilters:
        newString += "<div> <h3>" + str(typeFilters[idx]) + "<br>" + "</h3>"
        #print(typeFilters[idx])
        values = []
        noneValue = -1
        anotherValue = -1
        for x in dict.items():
            if x[0] == 'none':
                noneValue += x[1]
            elif x[0] == 'another':
                anotherValue += x[1]
            else:
                values.append((x[0], x[1]))
            #print(x[0], x[1], sep=" - ")
        #print()
        values.sort()
        if noneValue != -1:
            values.append(("none", noneValue))
        if anotherValue != -1:
            values.append(("another", anotherValue))

        lastStr = "0"
        newString += "<h2> <ul>"
        subLimita = 0
        for x in values:
            if(x[1] <= 3 and x[0] != "another" and x[0] != "none"):
                #print(x[0], " sub limita")
                subLimita += x[1]
                continue
            if x[0] != "none" and x[0] != "another" and (idx == 0 or idx == 6 or idx == 7):
                newString += "<li>" + lastStr + "  -  " + str(x[0]) + "  :  " + str(x[1]) + "</li>"
            else:
                if x[0] == "none":
                    newString += "<li>" + "Nu a fost specificat" + "  :  " + str(x[1]) + "</li>"
                else:
                    if x[0] == "another":
                        x = (x[0], x[1] + subLimita)
                    newString += "<li>" + str(x[0]) + "  :  " + str(x[1]) + "</li>"
            lastStr = str(x[0])
            #print(x[0], x[1], sep=" - ")
        #print()
        newString += "</ul> </h2> </div>"
        idx += 1

    finishValue = "{:.3f}".format(time.time() - start)
    newString += "<div style=\"padding-left: 4vw;\"> <h2> Rezultatul a fost generat in: " + str(finishValue) + "s<br> </h2> </div>"
    newString += "</div> </body> </html>"

    return newString

if __name__ == '__main__':
  app.run(debug=True)