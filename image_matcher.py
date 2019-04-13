import numpy as np
import cv2
import pickle
from collections import Counter


# OpenCV python binding does not define these
# https://docs.opencv.org/trunk/dc/d8c/namespacecvflann.html#a4e3e6c98d774ea77fd7f0045c9bc7817
FLANN_INDEX_LINEAR = 0
FLANN_INDEX_KDTREE = 1
FLANN_INDEX_KMEANS = 2
FLANN_INDEX_COMPOSITE = 3
FLANN_INDEX_KDTREE_SINGLE = 4
FLANN_INDEX_HIERARCHICAL = 5
FLANN_INDEX_LSH = 6
FLANN_INDEX_SAVED = 254
FLANN_INDEX_AUTOTUNED = 255
LINEAR = 0
KDTREE = 1
KMEANS = 2
COMPOSITE = 3
KDTREE_SINGLE = 4
SAVED = 254
AUTOTUNED = 255


# https://docs.opencv.org/2.4/modules/flann/doc/flann_fast_approximate_nearest_neighbor_search.html

# Works ONLY with ORB
DEFAULT_ORB_FLANN_INDEX_PARAMS = dict(algorithm=FLANN_INDEX_LSH,
                                      table_number=12,  # Docs recommend between 10 and 30
                                      key_size=9,  # Docs recommend between 10 and 20
                                      multi_probe_level=0)  # Use standard LSH; Docs recommend 2
DEFAULT_ORB_FLANN_SEARCH_PARAMS = dict()  # No params for ORB


class ImageMatcher:
    def __init__(self, feature_alg=None, flann_index_params=None, flann_search_params=None):
        if feature_alg is None:
            feature_alg = cv2.ORB_create(nfeatures=1024)  # cv default 500
        if flann_index_params is None:
            flann_index_params = DEFAULT_ORB_FLANN_INDEX_PARAMS
        if flann_search_params is None:
            flann_search_params = DEFAULT_ORB_FLANN_SEARCH_PARAMS
        self.feature_algorithm = feature_alg
        self.flann_index_params = flann_index_params
        self.flann_search_params = flann_search_params

        self.flann_index = None
        self.train_images_names = []
        self.train_images_descriptors = None
        self.index_list = []

    def build(self, image_names, cv_train_images):
        self.flann_index = cv2.flann_Index()
        self.train_images_names = []
        self.train_images_descriptors = None
        self.index_list = []
        for idx in range(len(image_names)):
            train_image = cv_train_images[idx]
            train_keypoints = self.feature_algorithm.detect(train_image, None)
            if not train_keypoints:
                print("Image: \"" + image_names[idx] + "\" is too simple for the FLANN index.")
                continue
            (train_keypoints, train_descriptors) = self.feature_algorithm.compute(train_image, train_keypoints)

            self.train_images_names.append(image_names[idx])

            if self.train_images_descriptors is not None:
                self.train_images_descriptors = np.concatenate((self.train_images_descriptors, train_descriptors))
            else:
                self.train_images_descriptors = train_descriptors

            descriptors_size = train_descriptors.shape[0]
            self.index_list.extend([idx] * descriptors_size)

        self.flann_index.build(self.train_images_descriptors, params=self.flann_index_params)

    def save(self, directory):
        if self.flann_index is None:
            raise RuntimeError("ImageMatcher.build() or load() must be called before calling save()!")
        # Uneeded as flan_index.load() wouldn't work below
        #self.flann_index.save(directory + "/index.flann")

        with open(directory + "/matcher.bin", "wb") as outfile:
            output_obj = dict(names=self.train_images_names,
                              descriptors=self.train_images_descriptors,
                              index_list=self.index_list)
            pickle.dump(output_obj, outfile)

    def load(self, directory):
        with open(directory + "/matcher.bin", "rb") as infile:
            input_obj = pickle.load(infile)
            self.flann_index = cv2.flann_Index()
            self.train_images_names = input_obj["names"]
            self.train_images_descriptors = input_obj["descriptors"]
            self.index_list = input_obj["index_list"]

        self.flann_index.build(self.train_images_descriptors, params=self.flann_index_params)
        # Could not get this to work
        #self.flann_index.load(self.train_images_descriptors, directory + "/index.flann")

    def match(self, cv_image, number_results=10):
        if self.flann_index is None:
            return []

        query_keypoints = self.feature_algorithm.detect(cv_image, None)
        if not query_keypoints:  # Query Image is too simple
            return None
        (query_keypoints, query_descriptors) = self.feature_algorithm.compute(cv_image, query_keypoints)

        (indices, dists) = self.flann_index.knnSearch(query_descriptors, knn=2, params=self.flann_search_params)

        # Apply D. Lowe's Ratio Test
        good_matches_idx = []
        for idx in range(len(dists)):
            (dist0, dist1) = dists[idx]
            if dist0 < 0.75 * dist1:
                good_matches_idx.append(indices[idx][0])  # Add only 1 of the matching indices

        if not good_matches_idx:
            return []

        # Majority Voting
        counts = np.asarray(self.index_list)[np.asarray(good_matches_idx)]
        votes = Counter(counts)
        likely_matches = votes.most_common()

        return [(self.train_images_names[idx], count) for (idx, count) in likely_matches[:number_results]]
