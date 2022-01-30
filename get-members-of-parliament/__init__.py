import logging

import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    import requests
    import time
    import json
    from bs4 import BeautifulSoup
    from bs4.dammit import EncodingDetector

    logging.info('Python HTTP trigger function processed a request.')
    
    result_list = []

    rooms = [1,2]
    for r in rooms:
        link = "http://www.cdep.ro/pls/parlam/structura2015.de?leg=2020&cam={}".format(r)
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
            result_list.append(to_append) 
    return func.HttpResponse(json.dumps(result_list),mimetype="application/json")

 #   if name:
 #       return func.HttpResponse(json.dumps(result_list),mimetype="application/json")
 #   else:
 #       return func.HttpResponse(
 #            "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
 #            status_code=200
 #       )
