import logging

import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    import requests
    import json
    from bs4 import BeautifulSoup
    from bs4.dammit import EncodingDetector

    legislature = req.params.get("leg")
    chamber = req.params.get("cham")
    member_id = req.params.get("id")

    # handle any missing parameter
    if not all([legislature, chamber, member_id]):
        return func.HttpResponse(
            "Please enter values for 'leg' (legislature), 'cham' (chamber) "
            + "and 'id' (member id) parameters, e.g. leg=2020&cham=2&id=17",
            status_code=406,
        )

    # handle wrong chamber value
    if chamber not in ["1", "2"]:
        return func.HttpResponse(
            "'cham' (chamber) value should be '1' or '2'",
            status_code=406,
        )

    link = "http://www.cdep.ro/pls/parlam/structura2015.mp?idm={}&cam={}&leg={}".format(  # noqa: E501
        member_id, chamber, legislature
    )

    req = requests.get(link)

    # handle wrong legislature value
    if req.status_code == 404:
        return func.HttpResponse(
            "Please enter a correct year value for leg (legislature).", status_code=406
        )

    # get the right encoding
    http_encoding = (
        req.encoding
        if "charset" in req.headers.get("content-type", "").lower()
        else None
    )
    html_encoding = EncodingDetector.find_declared_encoding(req.content, is_html=True)
    encoding = html_encoding or http_encoding

    soup = BeautifulSoup(req.content, "lxml", from_encoding=encoding)
    to_return = {}

    name = soup.find("title").text

    # handle wrong idm
    if not name.strip():
        return func.HttpResponse("Wrong id (parliament member id).", status_code=406)

    profile_div = soup.find("div", attrs={"class": "profile-pic-dep"})
    photo_link = "http://www.cdep.ro" + profile_div.find("img")["src"]
    birth_date = profile_div.text.strip()[2:].strip()
    to_return["name"] = name
    to_return["photo"] = photo_link
    to_return["dateOfBirth"] = birth_date
    return func.HttpResponse(json.dumps(to_return), mimetype="application/json")
