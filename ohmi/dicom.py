# -*- coding: utf-8 -*-
"""
Functions for reading, writing, and manipulating Dicom images.

Created on Wed Jan 13 13:15:54 2025

Copyright (c) 2025, Tommy Löfstedt. All rights reserved.

@author:  Tommy Löfstedt
@email:   tommy.lofstedt@umu.se
@license: BSD 3-clause.
"""
# import os
import sys
import abc
# import glob
import typing
import pathlib
import warnings

import tkinter as tk
from tkinter import ttk

import pydicom
import numpy as np
import matplotlib.pyplot as plt

import tree
import utils
import image
import errors

# print(__doc__)


if len(sys.argv) != 2:
    path = "/home/tommy/data/Data/Federated_Learning_Test_Sample/" + \
        "0a3b871660/CT/209768/"
    file = "CT 1.3.6.1.4.1.30071.8.4931001581895.7876809425404177307828748" + \
        "15224.dcm"
else:
    path = sys.argv[1]
    file = sys.argv[2]

path = pathlib.Path(path).resolve(strict=True)

assert path.is_dir()


# files = list(path.glob("*.dcm"))

# root = tree.Node("root")
# s0 = tree.Node("sub0", parent=root)
# s0b = tree.Node("sub0B", parent=s0)
# s0a = tree.Node("sub0A", parent=s0)
# s1 = tree.Node("sub1", parent=root)

# print(root.render())

# for node in tree.BFSIterator(root):
#     print(node.label)

# for node in tree.DFSIterator(root):
#     print(node.label)

# udo = tree.Node("Udo")
# marc = tree.Node("Marc", parent=udo)
# lian = tree.Node("Lian", parent=marc)
# dan = tree.Node("Dan", parent=udo)
# jet = tree.Node("Jet", parent=dan)
# jan = tree.Node("Jan", parent=dan)
# joe = tree.Node("Joe", parent=dan)

# print(udo.render())

# for node in tree.BFSIterator(udo):
#     print(node.label)

# for node in tree.DFSIterator(udo):
#     print(node.label)

# udo.parent = s1

# print(udo.render())
# print(root.render())

# for node in tree.BFSIterator(root):
#     print(node.label)

# for node in tree.DFSIterator(root):
#     print(node.label)


def build_tree(
               parent: tree.Node,
               ds: pydicom.dataset.Dataset,
               # parent: typing.Union[dict, None] = None,
               ) -> tree.Node:
    """Build a tree from a Dicom dataset.

    Parameters
    ----------
    tree : dict | None
        The dictionary tree object.
    ds : pydicom.dataset.Dataset
        The dataset object to add to the dict tree.
    parent : dict | None
        The parent dict in the tree (if any), default is `None` (no parent).
    """
    # For each DataElement in the current Dataset
    for idx, elem in enumerate(ds):
        # print(idx, elem)
        node = tree.Node(str(elem), elem, parent=parent)
        # parent.add(node)

        if elem.VR == "SQ":
            # DataElement is a sequence, containing 0 or more Datasets
            for seq_idx, seq_item in enumerate(elem.value):
                seq_label = f"{elem.name} Item {seq_idx + 1}"
                seq_node = tree.Node(seq_label, seq_item, parent=node)
                # node.add(seq_node)

                # Recurse into the sequence item(s)
                build_tree(seq_node, seq_item)

    return parent


def fix_siuid(SIUID: str,
              ):
    """Make sure that SIUIDs conform to the same format."""
    SIUID = SIUID.replace("/", "_")
    return SIUID


def read_dicom_slice(
        file: pathlib.Path,
        dtype: np.typing.DTypeLike = np.float32,
        escalation: errors.Escalation = errors.Escalation.WARNING,
        verbosity: int = utils.settings.verbosity,
        ) -> dict[str, typing.Union[list, image.Image]]:
    """Read a single Dicom file with an image slice."""
    if not file.is_file():
        raise ValueError(f"The file ('{str(file)}') is not a file.")

    try:
        # Read the DICOM file
        ds = pydicom.dcmread(file)
        if verbosity >= 3:
            print(build_tree(tree.Node("root"), ds).render())
    except pydicom.errors.InvalidDicomError:
        raise pydicom.errors.InvalidDicomError(
            f"Invalid Dicom file (can't load): {file}.")

    if not hasattr(ds, "SeriesInstanceUID"):
        raise pydicom.errors.InvalidDicomError(
            f"Invalid Dicom file found (no SeriesInstanceUID): {file}.")
    else:
        SIUID = fix_siuid(ds.SeriesInstanceUID)

    if not hasattr(ds, "Columns"):
        raise pydicom.errors.InvalidDicomError(
            f"Invalid Dicom file found (no Columns): {file}.")
    else:
        columns = ds.Columns

    if not hasattr(ds, "Rows"):
        raise pydicom.errors.InvalidDicomError(
            f"Invalid Dicom file found (no Rows): {file}.")
    else:
        rows = ds.Rows

    if not hasattr(ds, "PixelSpacing"):
        raise pydicom.errors.InvalidDicomError(
            f"Invalid Dicom file found (no PixelSpacing): {file}.")
    else:
        pixel_spacing = tuple(s.real for s in ds.PixelSpacing)

    if not hasattr(ds, "SliceThickness"):
        raise pydicom.errors.InvalidDicomError(
            f"Invalid Dicom file found (no SliceThickness): {file}.")
    else:
        slice_thickness = ds.SliceThickness.real

    if not hasattr(ds, "Modality"):
        raise pydicom.errors.InvalidDicomError(
            f"Invalid Dicom file found (no Modality): {file}.")
    else:
        modality = str(ds.Modality)

    return SIUID, ds, columns, rows, pixel_spacing, slice_thickness, modality


def read_directory(
        path: pathlib.Path,
        dtype: np.typing.DTypeLike = np.float32,
        escalation: errors.Escalation = errors.Escalation.WARNING,
        verbosity: int = utils.settings.verbosity,
        ) -> dict[str, image.Image]:
    """Read the Dicom files in a directory as one or more images."""
    if not path.is_dir():
        raise ValueError(f"The path ('{str(path)}') is not a directory.")

    # Find all files in the directory
    files = utils.find_files(path, "*", verbosity=verbosity)

    # If we are to print info, count the number of regular files in directory
    if verbosity > 0:
        count_files = 0
        for file in files:
            if file.is_file():
                count_files += 1
            else:
                print(file)
        utils.verbose("dicom.read_directory",
                      f"Found {count_files} (of {len(files)}) regular files "
                      f"in directory '{path}'.",
                      1, verbosity)

    def err_msg(where, message):
        errors.escalate(
            escalation,
            message,
            error_postfix="",
            warn_postfix=" Ignoring.",
            error=errors.InvalidDicomError,
            warning=UserWarning,
            nothing=lambda: utils.verbose(where, message, 2, verbosity),
            )

    images = dict()

    if len(files) == 0:
        return images
        # raise RuntimeError("No files found in this directory.")

    # First read all slices in the given directory
    num_images = 0
    num_slices = 0
    for file in files:
        if not file.is_file():
            continue  # Skip unless a regular file

        try:
            # print(file)
            SIUID, ds, columns, rows, pixel_spacing, slice_thickness, modality\
                = read_dicom_slice(file,
                                   dtype,
                                   escalation=escalation,
                                   verbosity=verbosity,
                                   )
            if SIUID not in images:
                images[SIUID] = {"Slices": [ds],
                                 "Columns": [columns],
                                 "Rows": [rows],
                                 "PixelSpacing": [pixel_spacing],
                                 "SliceThickness": [slice_thickness],
                                 "Modality": [modality]
                                 }
                num_images += 1
            else:
                images[SIUID]["Slices"].append(ds)
                images[SIUID]["Columns"].append(columns)
                images[SIUID]["Rows"].append(rows)
                images[SIUID]["PixelSpacing"].append(pixel_spacing)
                images[SIUID]["SliceThickness"].append(slice_thickness)
                images[SIUID]["Modality"].append(modality)
        except pydicom.errors.InvalidDicomError as e:
            err_msg("dicom.read_directory.read_dicom_slice", e.args[0])
            continue
        num_slices += 1

    utils.verbose("dicom.read_directory",
                  f"Read {num_slices} slices in {num_images} Dicom image(s) "
                  f"in directory '{path}'.",
                  1, verbosity)

    # Then order and check all the integrity of all images (series) found
    for SIUID in images:
        slices = images[SIUID]["Slices"]
        # Sort the slices by the slice location (physical location in machine)
        # TODO: Choice how to sort? Sorted by InstanceNumber before?
        slices = sorted(slices, key=lambda s: s.SliceLocation)
        images[SIUID]["Slices"] = slices

        for key, what in [["Columns", "columns"],
                          ["Rows", "rows"],
                          ["PixelSpacing", "spacings"],
                          ["SliceThickness", "thicknesses"],
                          ["Modality", "modalities"],
                          ]:
            # if len(set(seriesUIDs)) > 1:
            #     raise errors.InvalidDicomError("The images have different "
            #                                    "Series Instance UIDs.")
            if len(set(images[SIUID][key])) > 1:
                del images[SIUID]
                err_msg("dicom.read_directory",
                        f"The slice {what} are inconsistent ({SIUID}, "
                        f"'{file}'.")

        spacing = (*images[SIUID]["PixelSpacing"][0],
                   images[SIUID]["SliceThickness"][0])

        # TODO: Take ImageOrientation into account!
        shape = (images[SIUID]["Columns"][0],
                 images[SIUID]["Rows"][0],
                 len(images[SIUID]["Slices"]))

        modality = images[SIUID]["Modality"][0]

        # Create 3D array
        img = image.Image(path.name,
                          shape,
                          pixel_spacing=spacing,
                          series_id=SIUID,
                          modality=modality,
                          dtype=dtype)

        # Fill the image with the data from the Dicom files
        slices = images[SIUID]["Slices"]
        for i, slice_ in enumerate(slices):
            pixel_array = slice_.pixel_array.astype(dtype)

            if pixel_array.shape != shape[:-1]:
                raise errors.InvalidDicomError("The pixel array shapes are "
                                               "inconsistent.")

            img.set_slice(i, pixel_array)

        images[SIUID] = img

    return images

    # # plot 3 orthogonal slices
    # a1 = plt.subplot(2, 2, 1)
    # plt.imshow(img.data[:, :, img.shape[2] // 2])
    # a1.set_aspect(img.aspect_ratios(image.ImagePlane.AXIAL))

    # a2 = plt.subplot(2, 2, 2)
    # plt.imshow(img.data[:, img.shape[1] // 2, :])
    # a2.set_aspect(img.aspect_ratios(image.ImagePlane.SAGITTAL))

    # a3 = plt.subplot(2, 2, 3)
    # plt.imshow(img.data[img.shape[0] // 2, :, :].T)
    # a3.set_aspect(img.aspect_ratios(image.ImagePlane.CORONAL))

    # plt.show()


def find_all_dicom_files(
        path: pathlib.Path,
        dtype: np.typing.DTypeLike = np.float32,
        escalation: errors.Escalation = errors.Escalation.WARNING,
        verbosity: int = utils.settings.verbosity,
        ) -> dict[str, typing.Union[dict, image.Image]]:
    """Traverse a directory and find all Dicom files in it."""
    if not path.is_dir():
        raise ValueError(f"Provided path is not a directory ({path}).")

    # Load and parse all images in this directory
    dicoms = read_directory(path,
                            dtype=dtype,
                            escalation=escalation,
                            verbosity=verbosity,
                            )

    # Find subdirectories
    files = utils.find_files(path, "*", verbosity=verbosity)
    for file in files:
        if file.is_dir():
            # print(file)
            # Go through subdirectories recursively
            subdir_dicoms = find_all_dicom_files(file,
                                                 escalation=escalation,
                                                 verbosity=verbosity,
                                                 )
            for k in subdir_dicoms:
                # "DirectoryName/SeriesID"
                k_ = str(pathlib.Path(str(file.name), str(k)))
                # k_ = f"{file.name}/{k}"
                dicoms[k_] = subdir_dicoms[k]

    return dicoms


# def build_tk_tree(tree: ttk.Treeview,
#                   ds: pydicom.Dataset,
#                   parent: str = None,
#                   ) -> None:
#     """Build out the tree.

#     Parameters
#     ----------
#     tree : ttk.Treeview
#         The treeview object.
#     ds : pydicom.dataset.Dataset
#         The dataset object to add to the `tree`.
#     parent : str | None
#         The item ID of the parent item in the tree (if any), default ``None``.
#     """
#     # For each DataElement in the current Dataset
#     for idx, elem in enumerate(ds):
#         tree_item = tree.insert("", tk.END, text=str(elem))
#         if parent:
#             tree.move(tree_item, parent, idx)

#         if elem.VR == "SQ":
#             # DataElement is a sequence, containing 0 or more Datasets
#             for seq_idx, seq_item in enumerate(elem.value):
#                 tree_seq_item = tree.insert(
#                     "", tk.END, text=f"{elem.name} Item {seq_idx + 1}"
#                 )
#                 tree.move(tree_seq_item, tree_item, seq_idx)

#                 # Recurse into the sequence item(s)
#                 build_tk_tree(tree, seq_item, tree_seq_item)


# # Create the root Tk widget
# root = tk.Tk()
# root.geometry("1200x900")
# root.title(f"DICOM tree viewer - {path.name}")
# root.rowconfigure(0, weight=1)
# root.columnconfigure(0, weight=1)

# # Use a monospaced font
# s = ttk.Style()
# s.theme_use("clam")
# s.configure("Treeview", font=("Courier", 12))

# # Create the tree and populate it
# tree = ttk.Treeview(root)
# build_tk_tree(tree, ds, None)
# tree.grid(row=0, column=0, sticky=tk.NSEW)

# # Start the DICOM tree widget
# root.mainloop()
