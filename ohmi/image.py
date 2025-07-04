#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 15 13:54:38 2025

Copyright (c) 2025, Tommy Löfstedt. All rights reserved.

@author:  Tommy Löfstedt
@email:   tommy.lofstedt@umu.se
@license: BSD 3-clause.
"""
import enum
import typing

import numpy as np
import numpy.typing

__all__ = ["Image"]


class ImagePlane(enum.Enum):
    AXIAL = "AXIAL"
    SAGITTAL = "SAGITTAL"
    CORONAL = "CORONAL"


class Image(object):
    """A class for images.

    An image is oriented as Horizontal x Vertical x Depth.
    """

    def __init__(self,
                 name: str,
                 shape: tuple[int, ...],
                 pixel_spacing: tuple[float, ...] = None,
                 series_id: typing.Union[str, None] = None,
                 modality: typing.Union[str, None] = None,
                 dtype: np.typing.DTypeLike = np.float32,
                 ):

        if isinstance(shape, (tuple, list)):
            self._data = np.zeros(shape, dtype=dtype)
        else:
            raise ValueError("The shape must be a tuple of integers.")

        self.name = name
        self.pixel_spacing = pixel_spacing
        self.series_id = series_id
        self.modality = modality

    @property
    def name(self):
        """The name of the image."""
        return self._name

    @name.setter
    def name(self, value):
        """Set the name of the image."""
        self._name = str(value)

    @property
    def ndim(self):
        """The number of dimensions in the image."""
        return self.data.ndim

    @property
    def data(self):
        """The pixel array data of this image."""
        return self._data

    @property
    def shape(self):
        """The shape property of this image."""
        return self.data.shape

    @property
    def pixel_spacing(self):
        """The pixel spacing (distance between voxel centres) in the image."""
        return self._pixel_spacing

    @pixel_spacing.setter
    def pixel_spacing(self, value):
        """Set the pixel spacing (dist. between voxel centres) in the image."""
        if value is None:
            self._pixel_spacing = None
            self._aspect_ratios = None
        else:
            self._pixel_spacing = tuple(value)
            self._set_aspect_ratios(self.pixel_spacing)

    @property
    def series_id(self):
        """The series id of this image, if any."""
        return self._series_id

    @series_id.setter
    def series_id(self, value):
        """Set the value of series_id."""
        if value is None:
            self._series_id = value
        else:
            self._series_id = str(value)

    @property
    def modality(self):
        """The modality of this image, if any."""
        return self._modality

    @modality.setter
    def modality(self, value):
        """Set modality of this image, if any."""
        if value is None:
            self._modality = value
        else:
            self._modality = str(value)

    @property
    def dtype(self):
        """The dtype property of this image."""
        return self.data.dtype

    def aspect_ratios(self,
                      image_plane: typing.Union[ImagePlane, None] = None,
                      ):
        """Get the aspect ratio in the image."""
        if self.ndim == 1 or self.ndim == 2:
            return self._aspect_ratios
        elif self.ndim == 3:
            if image_plane is None:
                return self._aspect_ratios
            elif image_plane == ImagePlane.AXIAL:
                return self._aspect_ratios[0]
            elif image_plane == ImagePlane.SAGITTAL:
                return self._aspect_ratios[1]
            elif image_plane == ImagePlane.CORONAL:
                return self._aspect_ratios[2]
            else:
                raise ValueError("Unknown image plane. Must be of type "
                                 "`ImagePlane`.")
        else:
            raise ValueError("Number of image dimensions not supported!")

    def _set_aspect_ratios(self, pixel_spacing):
        if len(pixel_spacing) != self.ndim:
            raise ValueError(f"Pixel spacing must be provided for {self.ndim} "
                             f"dimensions.")
        if self.ndim == 1:
            self._aspect_ratios = None
        elif self.ndim == 2:
            self._aspect_ratios = pixel_spacing[1] / pixel_spacing[0]
        elif self.ndim == 3:
            self._aspect_ratios = [pixel_spacing[1] / pixel_spacing[0],  # ax
                                   pixel_spacing[1] / pixel_spacing[2],  # sag
                                   pixel_spacing[2] / pixel_spacing[0],  # cor
                                   ]
        else:
            raise ValueError("Number of image dimensions not supported!")

    def set_slice(self, index, data, copy=False):
        """Set a slice in the image."""
        # TODO: If time, need to adjust for the length of ndim and shapes.
        if (len(data.shape) != self.ndim - 1) or data.shape != self.shape[:-1]:
            return RuntimeError(f"Given slice has wrong size. Expected "
                                f"{self.shape[:-1]} but got {data.shape}.")
        index = int(index)
        if index < 0 or index > self.shape[-1] - 1:
            return IndexError("List index out of range.")

        if copy:
            self.data[..., index] = data.copy()
        else:
            self.data[..., index] = data

    def get_slice(self,
                  index: int,
                  image_plane: typing.Union[None, ImagePlane] = None,
                  copy: bool = False,
                  ):
        """Get a slice from the image."""
        index = int(index)

        if self.ndim == 2:
            num_slices = 1
        elif self.ndim == 3:
            if image_plane == ImagePlane.AXIAL:
                num_slices = self.shape[2]
            elif image_plane == ImagePlane.SAGITTAL:
                num_slices = self.shape[1]
            elif image_plane == ImagePlane.CORONAL:
                num_slices = self.shape[0]
            else:
                raise ValueError(f"Unknown image plane {str(image_plane)}.")
        else:
            raise ValueError("Need a 2D or 3D image to get a slice.")

        if index < 0 or index >= num_slices:
            return IndexError("List index out of range.")

        if self.ndim == 2:
            image = self.data
        elif image_plane == ImagePlane.AXIAL:
            image = self.data[:, :, index]
        elif image_plane == ImagePlane.SAGITTAL:
            image = self.data[:, index, :]
        elif image_plane == ImagePlane.CORONAL:
            image = self.data[index, :, :]
        else:
            raise RuntimeError("Cannot happen.")

        if copy:
            image = image.copy()

        return image

    def min(self):
        """Return the minimum intensity in the image."""
        return self.data.min()

    def max(self):
        """Return the maximum intensity in the image."""
        return self.data.max()
