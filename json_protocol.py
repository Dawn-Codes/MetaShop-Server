from enum import Enum
import base64
import numpy as np


class RequestType(Enum):
    IDENTIFY = "identify"
    PRICE_CHECK = "price_check"
    INVALID = "invalid"


def string_to_request_type(string):
    for request_type in RequestType.__members__.values():
        if string == request_type.value:
            return request_type
    return RequestType.INVALID


class ResponseType(Enum):
    IDENTIFY = "identify"
    PRICE_CHECK = "price_check"
    ERROR = "error"
    INVALID = "invalid"


def string_to_response_type(string):
    for response_type in ResponseType.__members__.values():
        if string == response_type.value:
            return response_type
    return ResponseType.INVALID


def build_json_request(request_type, obj):
    """
    For request_type=RequestType.IDENTIFY
        obj must be a list/tuple of image data lists/tuples [[img_bytes, ext_str], ...]
            img_bytes may be an list/array of uint8, bytes, or string characters
    For request_type=RequestType.PRICE_CHECK
        obj must be a list/tuple of integral MetaShop Product IDs [1, 2, 3, ...]
    """
    if not isinstance(request_type, RequestType):
        raise TypeError("build_json_request(request_type, obj): request_type must be a RequestType!")
    if request_type == RequestType.INVALID:
        raise TypeError("build_json_request(request_type, obj): request_type cannot be Invalid!")
    if not object:
        raise TypeError("build_json_request(request_type, obj): obj cannot be empty!")
    if request_type == RequestType.IDENTIFY:
        encoded_images = []
        for (img_bytes, ext) in obj:
            encoded_str = base64.b64encode(img_bytes).decode()
            encoded_images.append({"data": encoded_str, "extension": ext})
        return {"request_type": request_type.value, "images": encoded_images}
    if request_type == RequestType.PRICE_CHECK:
        return {"request_type": request_type.value, "metashop_ids": obj}


def build_json_response(response_type, obj):
    """
    For response_type=ResponseType.IDENTIFY
        obj must be a list of list such as (in the same order as given in the request):
        [['Product Name', 'MetaShop Product ID', 'Walmart SKU', 'Amazon ASIN', (img_bytes, ext_str)], ...]
            img_bytes may be an list/array of uint8, bytes, or string characters
    For response_type=ResponseType.PRICE_CHECK
        obj must be a list of lists such as (in the same order as given in the request):
        [[walmart_price, amazon_price], [walmart_price, amazon_price], ...]
    For response_type=ResponseType.ERROR
        obj must be a string
    """
    if not isinstance(response_type, ResponseType):
        raise TypeError("build_json_response(response_type, obj): response_type must be a ResponseType!")
    if response_type == ResponseType.INVALID:
        raise TypeError("build_json_response(response_type, obj): response_type cannot be Invalid!")
    if not object:
        raise TypeError("build_json_response(response_type, obj): obj cannot be empty!")
    if response_type == ResponseType.IDENTIFY:
        response_data = []
        for row in obj:
            (img_bytes, ext) = row[4]  # img_data
            encoded_str = base64.b64encode(img_bytes).decode()
            response_data.append({"product_name": row[0],
                                  "metashop_id": str(row[1]),
                                  "walmart_id": row[2],
                                  "amazon_id": row[3],
                                  "image": {"data": encoded_str, "extension": ext}})
        return {"response_type": response_type.value, "products": response_data}
    if response_type == ResponseType.PRICE_CHECK:
        response_data = []
        for row in obj:
            response_data.append({'walmart': row[0], "amazon": row[1]})
        return {"response_type": response_type.value, "prices": response_data}
    if response_type == ResponseType.ERROR:
        return {"response_type": response_type.value, "reason": obj}


def parse_json_request(dictionary):
    """
    Throws RuntimeError, binascii.Error
    """
    if not isinstance(dictionary, dict):
        raise TypeError("parse_json_request(dictionary): dictionary must be a dict!")
    if "request_type" not in dictionary or not isinstance(dictionary["request_type"], str):
        raise RuntimeError("Invalid JSON Request: doesn't contain \"request_type\" str field.")
    request_type = string_to_request_type(dictionary["request_type"])
    if request_type is RequestType.INVALID:
        raise RuntimeError("Invalid JSON Request: \"request_type\" str field contains invalid value.")
    if request_type is RequestType.IDENTIFY:
        if "images" not in dictionary or not isinstance(dictionary["images"], list):
            raise RuntimeError("Invalid JSON Request (identify): doesn't contain \"images\" array field.")
        images_field = dictionary["images"]
        image_datas = []
        for row in images_field:
            if not isinstance(row, dict):
                raise RuntimeError("Invalid JSON Request (identify): \"images\" array field doesn't contain "
                                   "only dict values.")
            if "data" not in row or not isinstance(row["data"], str):
                raise RuntimeError("Invalid JSON Request (identify): \"images\" array field must contain "
                                   "str field \"data\".")
            if "extension" not in row or not isinstance(row["extension"], str):
                raise RuntimeError("Invalid JSON Request (identify): \"images\" array field must contain "
                                   "str field \"extension\".")
            img_bytes = np.frombuffer(base64.b64decode(row["data"]), dtype=np.uint8)
            ext = row["extension"]
            image_datas.append((img_bytes, ext))
        return request_type, image_datas
    if request_type is RequestType.PRICE_CHECK:
        if "metashop_ids" not in dictionary or not isinstance(dictionary["metashop_ids"], list):
            raise RuntimeError("Invalid JSON Request (price_check): doesn't contain \"metashop_ids\" array field.")
        metashop_ids_field = dictionary["metashop_ids"]
        metashop_ids = []
        for id_field in metashop_ids_field:
            if not isinstance(id_field, str):
                raise RuntimeError("Invalid JSON Request (price_check): \"metashop_ids\" array field must contain "
                                   "str values.")
            metashop_ids.append(id_field)
        return request_type, metashop_ids


def parse_json_response(dictionary):
    """
    Throws RuntimeError, binascii.Error
    """
    if not isinstance(dictionary, dict):
        raise TypeError("parse_json_response(dictionary): dictionary must be a dict!")
    if "response_type" not in dictionary or not isinstance(dictionary["response_type"], str):
        raise RuntimeError("Invalid JSON Response: doesn't contain \"response_type\" str field.")
    response_type = string_to_response_type(dictionary["response_type"])
    if response_type is ResponseType.INVALID:
        raise RuntimeError("Invalid JSON Response: \"response_type\" str field contains invalid value.")
    if response_type is ResponseType.IDENTIFY:
        if "products" not in dictionary or not isinstance(dictionary["products"], list):
            raise RuntimeError("Invalid JSON Response (identify): doesn't contain \"products\" array field.")
        products_field = dictionary["products"]
        products = []
        for row in products_field:
            if not isinstance(row, dict):
                raise RuntimeError("Invalid JSON Response (identify): \"products\" array field doesn't contain "
                                   "only dict values.")
            if "product_name" not in row or not isinstance(row["product_name"], str):
                raise RuntimeError("Invalid JSON Response (identify): \"products\" dict field doesn't contain "
                                   "\"product_name\" str field.")
            if "metashop_id" not in row or not isinstance(row["metashop_id"], str):
                raise RuntimeError("Invalid JSON Response (identify): \"products\" dict field doesn't contain "
                                   "\"metashop_id\" str field.")
            if "walmart_id" not in row or not isinstance(row["walmart_id"], str):
                raise RuntimeError("Invalid JSON Response (identify): \"products\" dict field doesn't contain "
                                   "\"walmart_id\" str field.")
            if "amazon_id" not in row or not isinstance(row["amazon_id"], str):
                raise RuntimeError("Invalid JSON Response (identify): \"products\" dict field doesn't contain "
                                   "\"amazon_id\" str field.")
            if "image" not in row or not isinstance(row["image"], dict):
                raise RuntimeError("Invalid JSON Response (identify): \"products\" dict field doesn't contain "
                                   "\"image\" dict field.")
            image_dict = row["image"]
            if "data" not in image_dict or not isinstance(image_dict["data"], str):
                raise RuntimeError("Invalid JSON Response (identify): \"image\" dict field must contain "
                                   "str field \"data\".")
            if "extension" not in image_dict or not isinstance(image_dict["extension"], str):
                raise RuntimeError("Invalid JSON Response (identify): \"image\" dict field must contain "
                                   "str field \"extension\".")
            product_name = row["product_name"]
            metashop_id = row["metashop_id"]
            walmart_id = row["walmart_id"]
            amazon_id = row["amazon_id"]
            img_bytes = base64.b64decode(image_dict["data"])
            ext = image_dict["extension"]
            products.append([product_name, metashop_id, walmart_id, amazon_id, (img_bytes, ext)])
        return response_type, products
    if response_type is ResponseType.PRICE_CHECK:
        if "prices" not in dictionary or not isinstance(dictionary["prices"], list):
            raise RuntimeError("Invalid JSON Response (price_check): doesn't contain \"prices\" array field.")
        prices_field = dictionary["prices"]
        prices = []
        for row in prices_field:
            if not isinstance(row, dict):
                raise RuntimeError("Invalid JSON Response (price_check): \"prices\" array field doesn't contain "
                                   "only dict values.")
            if "walmart" not in row or not isinstance(row["walmart"], (int, float)):
                raise RuntimeError("Invalid JSON Response (price_check): \"prices\" dict field doesn't contain "
                                   "\"walmart\" int/float field.")
            if "amazon" not in row or not isinstance(row["amazon"], (int, float)):
                raise RuntimeError("Invalid JSON Response (price_check): \"prices\" dict field doesn't contain "
                                   "\"amazon\" int/float field.")
            prices.append([row["walmart"], row["amazon"]])
        return response_type, prices
    if response_type is ResponseType.ERROR:
        if "reason" not in dictionary or not isinstance(dictionary["reason"], str):
            raise RuntimeError("Invalid JSON Response (error): doesn't contain \"reason\" str field.")
        return response_type, dictionary["reason"]
