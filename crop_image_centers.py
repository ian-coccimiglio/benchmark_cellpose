#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 25 22:51:52 2024.

@author: ian
"""

from skimage.io import imread, imsave
import os
import numpy as np


def max_crop(im):
    """
    Choose a maximum crop-size for a center-square of the image.
    """
    maximum_size = np.min([im.shape[0], im.shape[1]])
    return maximum_size


def center_crop(im: np.ndarray, crop_size=10):
    """
    Crops an image from the center by `crop_size` pixels
    Generates a box with width and height 2*crop_size
    """
    center_x, center_y = im.shape[0] // 2, im.shape[1] // 2
    x_left, x_right = center_x - (crop_size // 2), center_x + (crop_size // 2)
    x_top, x_bottom = center_y - (crop_size // 2), center_y + (crop_size // 2)
    ind = np.s_[x_left:x_right, x_top:x_bottom]
    cropped_image = im[ind]
    return cropped_image


file_path = "images/cell_00505_neur_ips_2160.tif"
crop_output_path = "images/"


def main(file_path, crop_output_path):
    sample_name = file_path.split("/")[-1].split("_2160")[0]
    im = imread(file_path)
    max_sample_crop = 2500
    if max_sample_crop > max_crop(im):
        print("Crop size too big, stopping at maximum crop")
        max_sample_crop = max_crop(im)
    image_list = [
        center_crop(im, size) for size in range(224, max_sample_crop, 224)
    ]
    for image in image_list:
        output_path = os.path.join(
            crop_output_path,
            sample_name + f"_{str(image.shape[0]).zfill(4)}.tif",
        )
        imsave(
            output_path,
            image,
        )


if __name__ == "__main__":
    main(file_path, crop_output_path)
