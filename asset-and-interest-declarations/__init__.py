import logging

import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    import requests
    import time
    import json
    from bs4 import BeautifulSoup

    lastname_firstname = req.params.get("name")

    if lastname_firstname:
        result_list = []

        headers = {
            "Host": "declaratii.integritate.eu",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36",  # noqa: E501
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Faces-Request": "partial/ajax",
            "Content-type": "application/x-www-form-urlencoded;charset=UTF-8",
            "Content-Length": "816",
            "Origin": "http://declaratii.integritate.eu",
            "Connection": "keep-alive",
            "Referer": "http://declaratii.integritate.eu/",
        }

        link = "http://declaratii.integritate.eu/index.html"

        session = requests.Session()

        resp_req = session.get(link)
        rsoup = BeautifulSoup(resp_req.content, "lxml")
        vstate = rsoup.find("input", attrs={"name": "javax.faces.ViewState"}).get(
            "value"
        )
        cwindow = rsoup.find("input", attrs={"name": "javax.faces.ClientWindow"}).get(
            "value"
        )
        icewindow = rsoup.find("input", attrs={"name": "ice.window"}).get("value")
        iceview = rsoup.find("input", attrs={"name": "ice.view"}).get("value")

        data = {
            "form": "form",
            "form:searchField_input": "numePrenume",
            "javax.faces.source": "form:submitButtonSS",
            "javax.faces.partial.execute": "@all",
            "javax.faces.partial.render": "@all",
            "ice.focus": "form:submitButtonSS",
            "form:submitButtonSS": "caută>",
            "ice.event.target": "form:submitButtonSS",
            "ice.event.captured": "form:submitButtonSS",
            "ice.event.type": "onclick",
            "ice.event.alt": "false",
            "ice.event.ctrl": "false",
            "ice.event.shift": "false",
            "ice.event.meta": "false",
            "ice.event.x": "466",
            "ice.event.y": "497",
            "ice.event.left": "true",
            "ice.event.right": "false",
            "javax.faces.behavior.event": "click",
            "javax.faces.partial.event": "click",
            "javax.faces.partial.ajax": "true",
        }

        data["form:searchKey_input"] = lastname_firstname
        data["javax.faces.ViewState"] = vstate
        data["javax.faces.ClientWindow"] = cwindow
        data["ice.window"] = icewindow
        data["ice.view"] = iceview

        resp = session.post(link, headers=headers, data=data)
        soup = BeautifulSoup(resp.content, "lxml")

        data["form:resultsTable"] = "form:resultsTable"
        data["form:resultsTable_paging"] = "true"
        data["form:resultsTable_rows"] = "100"
        data["javax.faces.source"] = "form:resultsTable"
        data["javax.faces.partial.execute"] = "form:resultsTable"
        data["javax.faces.partial.render"] = "form:resultsTable"
        data["ice.focus"] = "form:resultsTable_paginatorbottom_current_page"
        data["ice.event.captured"] = "form:resultsTable"
        data["ice.event.target"] = ""
        data["form:typeIn"] = "csv"
        del data["form:submitButtonSS"]
        del data["javax.faces.behavior.event"]
        del data["javax.faces.partial.event"]

        results = int(soup.find("span", id="form:_t90").text)
        added = 0
        page = 1

        while added < results:
            data["form:resultsTable_page"] = page
            resp = session.post(link, headers=headers, data=data)
            soup = BeautifulSoup(resp.content, "lxml")
            trs = soup.findAll("tr", {"tabindex": True})
            for tr in trs:
                tds = tr.findAll("td")
                url = tds[7].a["href"].replace(" ", "%20")
                id = url.split("uniqueIdentifier=")[1]
                full_url = "http://declaratii.integritate.eu" + url
                to_append = {}
                for idx, val in enumerate(
                    [
                        "name",
                        "institution",
                        "function",
                        "locality",
                        "county",
                        "date",
                        "declaration",
                    ]
                ):
                    to_append[val] = tds[idx].text
                to_append["link"] = full_url
                to_append["uniqueIdentifier"] = id
                result_list.append(to_append)
                added += 1
            page += 1
            time.sleep(1)
        return func.HttpResponse(json.dumps(result_list), mimetype="application/json")
    else:
        return func.HttpResponse(
            "Please enter a value for 'name' (last name and first name) parameter, "
            + "e.g. lastname_firstname=Ionescu Marian",
            status_code=406,
        )
