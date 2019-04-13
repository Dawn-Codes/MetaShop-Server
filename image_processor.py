import threading
import cv2

from image_matcher import ImageMatcher
import image_util


class ImageProcessor:
    def __init__(self):
        self.lock = threading.Lock()
        self.image_matcher = ImageMatcher()

    def match_image(self, image_data):
        try:
            cv_image = image_util.load_cv_image_from_image_bytes(image_data)
            if cv_image is None:
                print("Could not decode image!")
                return []
        except cv2.error as ex:
            print(ex)
            print("Could not decode image!")
            return []
        self.lock.acquire()
        results = self.image_matcher.match(cv_image, 5)
        self.lock.release()
        return results

    def update_image_matcher(self, image_matcher):
        self.lock.acquire()
        self.image_matcher = image_matcher
        self.lock.release()
