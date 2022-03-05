import logging

import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    import requests
    import json
    from bs4 import BeautifulSoup
    from bs4.dammit import EncodingDetector

    legislature = req.params.get("legislature")
    # chamber = 1 (get senators)
    # chamber = 2 (get deputies)
    # chamber = 3 (get all members)
    chamber = req.params.get("chamber")

    # set default values for parameters
    if not legislature:
        legislature = "2020"
    if not chamber:
        chamber = "3"

    chamber_dict = {
        "1": ("senators", [1]),
        "2": ("deputies", [2]),
        "3": ("all members", [1, 2]),
    }

    result_list = []

    try:
        chamber_set = chamber_dict[chamber]
    except KeyError:
        # handle wrong chamber exception
        return func.HttpResponse(
            "Parameter 'chamber' can only be 1 (senators), 2 (deputies) or 3 (all members)",  # noqa: E501
            status_code=406,
        )

    for chamber in chamber_set[1]:
        link = "http://www.cdep.ro/pls/parlam/structura2015.de?leg={}&cam={}".format(
            legislature, chamber
        )
        req = requests.get(link)

        # handle wrong legislature value
        if req.status_code == 404:
            return func.HttpResponse(
                "Please enter a correct year value for parameter 'legislature'",
                status_code=406,
            )

        # get the right encoding
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
            result_list.append(
                getResult(row, chamber),
            )
        final_dict = {
            "legislature": int(legislature),
            "profileUrl": "http://www.cdep.ro/pls/parlam/structura2015.mp"
            + "?idm=:id&cam=:chamber&leg={leg}".format(leg=legislature),
            "results": result_list,
        }
    return func.HttpResponse(json.dumps(final_dict), mimetype="application/json")


def getResult(row, chamber):
    to_append = {}

    entries = row.findAll("a")

    to_append["name"] = entries[0].text

    try:
        to_append["party"] = entries[2].text
        to_append["district"] = entries[1].text.split("/")[1].strip()
    except IndexError:
        to_append["party"] = entries[1].text

    to_append["chamber"] = chamber

    profile_url = entries[0]["href"]
    member_id = profile_url.split("idm=")[1].split("&")[0]

    try:
        to_append["id"] = int(member_id)
    except ValueError:
        to_append["id"] = member_id

    return to_append
