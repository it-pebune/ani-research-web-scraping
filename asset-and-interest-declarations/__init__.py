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
        # replace dash with space
        lastname_firstname = lastname_firstname.replace("-", " ")
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

        # GET request to main page to collect elements needed for POST
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

        # prepare POST data
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

        # POST request
        resp = session.post(link, headers=headers, data=data)
        soup = BeautifulSoup(resp.content, "lxml")

        # if no results, return error message
        no_results = soup.find("h5", text="Nu s-au găsit rezultate")
        if no_results:
            return func.HttpResponse("No results found", status_code=204)

        # if too many results, return error message
        too_many_results = soup.find("span", attrs={"id": "_t133"})
        if too_many_results:
            return func.HttpResponse("More than 10 000 results found", status_code=413)

        # Prepare POST data for looping through results page
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

        results = int(soup.find("span", id="form:_t91").text)
        added = 0
        page = 1

        # assuming there are multiple result pages
        multiple_result_pages = True

        # looping through result pages and appending data for each result
        while added < results and multiple_result_pages:
            # if only one page, than use the initial fetched page
            if results <= 25:
                multiple_result_pages = False
            # if multiple pages, fetch each
            else:
                data["form:resultsTable_page"] = page
                resp = session.post(link, headers=headers, data=data)
                soup = BeautifulSoup(resp.content, "lxml")
            trs = soup.findAll("tr", {"tabindex": True})
            for tr in trs:
                tds = tr.findAll("td")
                url = tds[7].a["href"].replace(" ", "%20")
                file_name = url.split("fileName=")[1].split("&")[0]
                uid = url.split("uniqueIdentifier=")[1]
                to_append = {}
                for idx, val in enumerate(
                    [
                        "name",
                        "institution",
                        "function",
                        "locality",
                        "county",
                        "date",
                        "type",
                    ]
                ):
                    to_append[val] = getValue(tds, idx)
                to_append["filename"] = file_name
                to_append["uid"] = uid
                result_list.append(to_append)
                added += 1
            page += 1
            time.sleep(1)
        final_dict = {
            "downloadUrl": "http://declaratii.integritate.eu/DownloadServlet"
            + "?fileName=:filename&uniqueIdentifier=:uid",
            "results": result_list,
        }
        return func.HttpResponse(json.dumps(final_dict), mimetype="application/json")
    else:
        return func.HttpResponse(
            "Please enter a value for parameter 'name' (last name and first name), "
            + "e.g. name=Ionescu Marian",
            status_code=406,
        )


def getValue(tds, idx):
    if tds[idx].text == "Declaratie de avere":
        return "A"  # Declaratie de avere
    if tds[idx].text == "Declaratie de interese":
        return "I"  # Declaratie de interese
    return tds[idx].text
