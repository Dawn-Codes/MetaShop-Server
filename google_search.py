import requests
import difflib
import re

GOOGLE_CUSTOM_SEARCH_RESTRICTED_URL = "https://www.googleapis.com/customsearch/v1/siterestrict"
GOOGLE_CUSTOM_SEARCH_API_KEY = "AIzaSyABR-oFbPSwX_U_61UZHWqqFaqaGNt62n0"
WALMART_CUSTOM_SEARCH_ENGINE_ID = "010075545656909996673:cfr_n3qhsfc"
AMAZON_CUSTOM_SEARCH_ENGINE_ID = "010075545656909996673:3zcndga3nbc"


def search(query, custom_search_engine):
    """
    Performs a Google Custom Search.
    If there are any errors possible exceptions may be thrown: requests.exceptions.HTTPError,
    requests.exceptions.ConnectionError, requests.exceptions.Timeout, or requests.exceptions.RequestException.
    :param query: Keywords to search.
    :param custom_search_engine: Either WALMART_CUSTOM_SEARCH_ENGINE_ID or AMAZON_CUSTOM_SEARCH_ENGINE_ID.
    :return: Many-tiered lists and dictionaries of Google Search data.
    """
    params = {"key": GOOGLE_CUSTOM_SEARCH_API_KEY, "cx": custom_search_engine, "q": query}

    r = requests.get(url=GOOGLE_CUSTOM_SEARCH_RESTRICTED_URL, params=params)
    return r.json()


def search_walmart_product_info(query):
    """
    Performs a Google Custom Search over Walmart.com to extract relevant product info.
    If there are any errors possible exceptions may be thrown: requests.exceptions.HTTPError,
    requests.exceptions.ConnectionError, requests.exceptions.Timeout, or requests.exceptions.RequestException.
    :param query: Product keywords to search.
    :return: A list of list containing: [ ['Product Name', 'Walmart SKU', 'Image URL'], ... ].
    """
    query_results = search(query, WALMART_CUSTOM_SEARCH_ENGINE_ID)
    info = []
    if "items" in query_results:
        for entry in query_results["items"]:
            if "pagemap" in entry and "product" in entry["pagemap"] and entry["pagemap"]["product"]\
                    and "name" in entry["pagemap"]["product"][0]\
                    and "sku" in entry["pagemap"]["product"][0]\
                    and "image" in entry["pagemap"]["product"][0]:
                info.append([
                    entry["pagemap"]["product"][0]["name"],
                    entry["pagemap"]["product"][0]["sku"],
                    entry["pagemap"]["product"][0]["image"]
                ])

    return info


def search_amazon_product_info(query):
    """
    Performs a Google Custom Search over Amazon.com to extract relevant product info.
    If there are any errors possible exceptions may be thrown: requests.exceptions.HTTPError,
    requests.exceptions.ConnectionError, requests.exceptions.Timeout, or requests.exceptions.RequestException.
    :param query: Product keywords to search.
    :return: A list of list containing: [ ['Product Name', 'Amazon ASIN', 'Image URL'], ... ].
    """
    query_results = search(query, AMAZON_CUSTOM_SEARCH_ENGINE_ID)
    info = []
    if "items" in query_results:
        for entry in query_results["items"]:
            if "pagemap" in entry and "metatags" in entry["pagemap"] and entry["pagemap"]["metatags"]\
                    and "og:title" in entry["pagemap"]["metatags"][0]\
                    and "og:url" in entry["pagemap"]["metatags"][0] and entry["pagemap"]["metatags"][0]["og:url"]\
                    and "og:image" in entry["pagemap"]["metatags"][0]:
                info.append([
                    entry["pagemap"]["metatags"][0]["og:title"],
                    entry["pagemap"]["metatags"][0]["og:url"][25:35],  # http://www.amazon.com/dp/B009MGXDZW/ref=tsm_1_fb_lk
                    entry["pagemap"]["metatags"][0]["og:image"]
                ])

    return info

import pprint


def get_closest_match(query, product_infos):
    """
    Given the original product query and product_infos returned from either search_walmart_product_info() or
    search_amazon_product_info(), performs a textual match to find which result is closest.
    :param query: Original search query containing the product keywords to search.
    :param product_infos: A list of list containing: [ ['Product Name', 'Store SKU', 'Image URL'], ... ].
    :return: The closest product_info containing: ['Product Name', 'Store SKU', 'Image URL'].
    """
    if not product_infos:
        return None
    #pprint.pprint(product_infos)
    ratios = len(product_infos) * [0]
    for i in range(len(product_infos)):
        matcher = difflib.SequenceMatcher(a=query.lower(), b=product_infos[i][0].lower())
        ratios[i] += matcher.ratio()
    #print(ratios)
    return product_infos[ratios.index(max(ratios))]


def verify_walmart_product_info(product_info):
    """
    Performs data sanitization on a product_info list.
    :param product_info: List containing: ['Product Name', 'Walmart SKU', 'Image URL'].
    :return: A corrected list containing: ['Product Name', 'Walmart SKU', 'Image URL'] or None if the data was invalid.
    """
    if not product_info:
        return None
    correct_info = 3 * [None]

    correct_info[0] = product_info[0]  # Can't really verify name if incorrect

    if not product_info[1].isdigit():  # Walmart SKU must be all numbers
        return None
    correct_info[1] = product_info[1]

    # Set maximum image length to 560^2 in image URL (gets a decently sized cached copy from Walmart)
    correct_info[2] = re.sub(r"(odn\w+=)\d+", r"\g<1>560", product_info[2])

    return correct_info


def verify_amazon_product_info(product_info):
    """
    Performs data sanitization on a product_info list.
    :param product_info: List containing: ['Product Name', 'Amazon ASIN', 'Image URL'].
    :return: A corrected list containing: ['Product Name', 'Amazon ASIN', 'Image URL'] or None if the data was invalid.
    """
    if not product_info:
        return None
    correct_info = 3 * [None]

    correct_info[0] = product_info[0]  # Can't really verify name if incorrect

    if len(product_info[1]) != 10:  # Amazon ASIN must be 10 letters and/or numbers
        return None
    correct_info[1] = product_info[1]

    img_url = product_info[2]
    # Remove extraneous parts of image URL (it performs various dynamic operations to the picture we don't need)
    correct_info[2] = img_url[:img_url.find("._")] + img_url[img_url.rfind("_.") + 1:]

    return correct_info


def search_retailers(query):
    """
    Searches Walmart.com and Amazon.com for the closest product info that matches query.
    If there are any errors possible exceptions may be thrown: requests.exceptions.HTTPError,
    requests.exceptions.ConnectionError, requests.exceptions.Timeout, or requests.exceptions.RequestException.
    :param query: Search query containing the product keywords to search.
    :return: A dictionary containing {'walmart': ['Product Name', 'Walmart SKU', 'Image URL'],
    'amazon': ['Product Name', 'Amazon ASIN', 'Image URL']}. The dictionary values can be None.
    """
    walmart_infos = search_walmart_product_info(query)
    walmart_match = get_closest_match(query, walmart_infos)
    walmart_match = verify_walmart_product_info(walmart_match)

    amazon_infos = search_amazon_product_info(query)
    amazon_match = get_closest_match(query, amazon_infos)
    amazon_match = verify_amazon_product_info(amazon_match)

    print(walmart_match)
    print(amazon_match)
    return {'walmart': walmart_match, 'amazon': amazon_match}


def test_search():  # Debug
    print("Enter product information:")
    query = input("> ")
    print("\n\"" + query + '"')

    info = search_walmart_product_info(query)

    print("\nWalmart")
    for i in range(len(info)):
        info[i] = verify_walmart_product_info(info[i])
        print(info[i])

    closest_info = get_closest_match(query, info)
    print('\n', closest_info, sep='')

    info = search_amazon_product_info(query)

    print("\nAmazon")
    for i in range(len(info)):
        info[i] = verify_amazon_product_info(info[i])
        print(info[i])

    closest_info = get_closest_match(query, info)
    print('\n', closest_info, sep='')
