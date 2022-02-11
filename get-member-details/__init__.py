import logging

import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    import requests
    import time
    import json
    from bs4 import BeautifulSoup
    from bs4.dammit import EncodingDetector
    

    member_id = req.params.get('id')
    
    if not member_id:
        return func.HttpResponse(
             "Please enter a value for id parameter",
             status_code=200
        )
    
    id_elements = member_id.split("-")
    link = "http://www.cdep.ro/pls/parlam/structura2015.mp?idm={}&cam={}&leg={}".format(id_elements[2],id_elements[0], id_elements[1])
    
    req = requests.get(link)
    http_encoding = req.encoding if 'charset' in req.headers.get('content-type', '').lower() else None
    html_encoding = EncodingDetector.find_declared_encoding(req.content, is_html=True)
    encoding = html_encoding or http_encoding
    soup = BeautifulSoup(req.content, "lxml",from_encoding=encoding)
    to_return = {}
    name = soup.find("title").text
    profile_div = soup.find("div",attrs={"class": "profile-pic-dep"})
    photo_link = "http://www.cdep.ro" + profile_div.find("img")['src']
    birth_date = profile_div.text.strip()[2:].strip()
    to_return['name'] = name
    to_return['photo_link'] = photo_link
    to_return['birth_date'] = birth_date
    return func.HttpResponse(json.dumps(to_return),mimetype="application/json")

