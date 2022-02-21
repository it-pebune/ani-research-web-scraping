import logging

import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    import requests
    import json
    from bs4 import BeautifulSoup
    from bs4.dammit import EncodingDetector

    legislature = req.params.get("leg")
    # cham = 1 (get senators)
    # cham = 2 (get deputies)
    # cham = 3 (get all members)
    chamber = req.params.get("cham")

    if not legislature:
        legislature = "2020"
    if not chamber:
        chamber = "3"

    chamber_dict = {
        "1": ("get senators", ["1"]),
        "2": ("get deputies", ["2"]),
        "3": ("get all members", ["1", "2"]),
    }

    result_list = []

    chamber_set = chamber_dict[chamber]

    for chamber in chamber_set[1]:
        link = "http://www.cdep.ro/pls/parlam/structura2015.de?leg={}&cam={}".format(
            legislature, chamber
        )
        req = requests.get(link)
        http_encoding = (
            req.encoding
            if "charset" in req.headers.get("content-type", "").lower()
            else None
        )
        html_encoding = EncodingDetector.find_declared_encoding(
            req.content, is_html=True
        )
        encoding = html_encoding or http_encoding
        soup = BeautifulSoup(req.content, "lxml", from_encoding=encoding)
        rows = soup.find("tbody").findAll("tr")
        for row in rows:
            to_append = {}
            entries = row.findAll("a")
            to_append["name"] = entries[0].text
            try:
                to_append["party"] = entries[2].text
                to_append["location"] = entries[1].text.split("/")[1].strip()
            except IndexError:
                to_append["party"] = entries[1].text
            to_append["legislature"] = legislature
            if chamber == "1":
                to_append["chamber"] = "senat"
            else:
                to_append["chamber"] = "cdep"
            profile_url = "http://www.cdep.ro" + entries[0]["href"]
            member_id = profile_url.split("idm=")[1].split("&")[0]
            to_append["id"] = member_id
            to_append["link"] = profile_url
            result_list.append(to_append)
        final_dict = {
            "action": chamber_set[0],
            "legislature": legislature,
            "results": result_list,
        }
    return func.HttpResponse(json.dumps(final_dict), mimetype="application/json")
