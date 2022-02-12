import logging

import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    import requests
    import time
    import json
    from bs4 import BeautifulSoup
    from bs4.dammit import EncodingDetector

    logging.info('Python HTTP trigger function processed a request.')
    
    
    # cam = 1 - get senators
    # cam = 2 - get deputies
    # cam = 3 - get all members 

    cam = req.params.get('cam')
    leg = req.params.get('leg')
    
    if not leg:
        leg = "2020"
    cam_dict = {"1":("get senators",["1",]), "2":("get deputies",["2",]), "3":("get all members",["1","2"])}

    if not cam:
        cam = "3"

    result_list = []
    cam_set = cam_dict[cam]

    for r in cam_set[1]:
        link = "http://www.cdep.ro/pls/parlam/structura2015.de?leg={}&cam={}".format(leg, r)
        req = requests.get(link)
        http_encoding = req.encoding if 'charset' in req.headers.get('content-type', '').lower() else None
        html_encoding = EncodingDetector.find_declared_encoding(req.content, is_html=True)
        encoding = html_encoding or http_encoding
        soup = BeautifulSoup(req.content, "lxml",from_encoding=encoding)
        rows = soup.find('tbody').findAll("tr")
        for row in rows:
            to_append = {}
            entries = row.findAll("a")
            to_append['name'] = entries[0].text
            try:  
                to_append['party'] = entries[2].text              
                to_append['location'] = entries[1].text.split("/")[1].strip()
            except IndexError:
                to_append['party'] = entries[1].text  
            if r == 1:
                to_append['room'] = "senat"
            else:
                to_append['room'] = "cdep"
            profile_url = "http://www.cdep.ro" + entries[0]['href']
            to_append['link'] = profile_url
            member_id = profile_url.split("idm=")[1].split("&")[0]
            to_append['id'] = "{}-{}-{}".format(r,leg, member_id)
            result_list.append(to_append) 
        final_dict = {"action":cam_set[0], "leg": leg, "results": result_list}
    return func.HttpResponse(json.dumps(final_dict),mimetype="application/json")
