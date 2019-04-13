import requests

WALMART_PRODUCT_LOOKUP_URL = "http://api.walmartlabs.com/v1/items"
WALMART_API_KEY = "34y2xpg5kysqswrg2tc9frh4"


def lookup_walmart_prices(walmart_skus):
    """
    Performs a Walmart price search by using the Walmart Product Lookup API.
    *Limited to 20 items per call
    *Limited to 5 lookups per second
    :param walmart_skus: List of store-specific Walmart SKUs that are used to find the products prices.
    :return: List of prices for each Walmart SKU.
    """
    if len(walmart_skus) > 20:
        raise TypeError("Walmart API can only handle 20 products maximum!")
    params = {"ids": ','.join(map(str, walmart_skus)), "apiKey": WALMART_API_KEY}
    r = requests.get(url=WALMART_PRODUCT_LOOKUP_URL, params=params)
    if r.status_code == 403:  # 403 Forbidden; is most likely because the 5 lookups/second has been reached
        raise RuntimeError(r.text)
    json = r.json()
    if "errors" in json and json["errors"]:
        raise RuntimeError("Walmart API Error: " + str(json))
    prices = []
    for item in json["items"]:
        prices.append(item["salePrice"])
    return prices


AMAZON_WEBSERVICES_REGION_TOP_LEVEL_DOMAIN = "com"  # For US Amazon
AMAZON_WEBSERVICES_HOST = "webservices.amazon." + AMAZON_WEBSERVICES_REGION_TOP_LEVEL_DOMAIN
AMAZON_WEBSERVICES_ENDPOINT = "/onca/xml"
AMAZON_WEBSERVICES_URL = "http://" + AMAZON_WEBSERVICES_HOST + AMAZON_WEBSERVICES_ENDPOINT
AMAZON_ACCESS_KEY = "AKIAI5X2KZ5KFR2IZZLA"
AMAZON_SECRET_KEY = "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"
#AMAZON_ASSOCIATE_ID = "metashop02-20"


def lookup_amazon_prices(amazon_asins):
    canonicalized_query = "test_query"

    string_to_sign = "GET\n" +\
                     AMAZON_WEBSERVICES_HOST + '\n' +\
                     AMAZON_WEBSERVICES_ENDPOINT + '\n' +\
                     canonicalized_query

    print(string_to_sign)
    return None
