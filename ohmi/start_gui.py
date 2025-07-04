#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 16 14:33:42 2025

Copyright (c) 2025, Tommy Löfstedt. All rights reserved.

@author:  Tommy Löfstedt
@email:   tommy.lofstedt@umu.se
@license: BSD 3-clause.
"""
import sys
import typing
import pathlib
import threading

# from PySide2 import QtGui
from PySide2 import QtWidgets

from gui.main import Ui_MainWindow

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

import utils
import dicom
import image
import errors


class MplCanvas(FigureCanvasQTAgg):
    """A Matplotlib window."""

    class IndexTracker:
        """Keep track of the slice index in an axis."""

        def __init__(self, parent, plane_axes,
                     speed=1,
                     interval=0.05):
            self.parent = parent

            self.plane_axes = plane_axes

            self.speed = int(speed)
            self.interval = float(interval)

            self.timer = None

        def update_timer(self, *args):
            """Set a timer to update the image."""
            if (self.timer is not None) and self.timer.is_alive():
                self.timer.cancel()

            self.timer = threading.Timer(self.interval,
                                         self.parent.increase_index,
                                         args=args,
                                         )
            self.timer.start()

        def on_scroll(self, event):
            """Handle the scroll event."""
            for image_plane, axis in self.plane_axes:
                if event.inaxes == axis:
                    if event.button == 'up':
                        change = 1
                    else:
                        change = -1

                    self.update_timer(change, image_plane)

    def __init__(self, parent=None, width=12, height=8, dpi=300):

        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = [[None, None],
                     [None, None]]
        self.axes[0][0] = fig.add_subplot(221)
        self.axes[0][1] = fig.add_subplot(222)  # , sharey=self.axes[0][0])
        self.axes[1][0] = fig.add_subplot(223)  # , sharex=self.axes[0][0])

        self.tracker_ax = self.IndexTracker(
            self,
            [(image.ImagePlane.AXIAL, self.axes[0][0]),
             (image.ImagePlane.SAGITTAL, self.axes[0][1]),
             (image.ImagePlane.CORONAL, self.axes[1][0]),
             ],
            )
        fig.canvas.mpl_connect('scroll_event', self.tracker_ax.on_scroll)

        # self.tracker_sag = self.IndexTracker(
        #     self, image.ImagePlane.SAGITTAL, self.axes[0][1], "Upper Right")
        # fig.canvas.mpl_connect('scroll_event', self.tracker_sag.on_scroll)

        # self.tracker_cor = self.IndexTracker(
        #     self, image.ImagePlane.CORONAL, self.axes[1][0], "Lower Left")
        # fig.canvas.mpl_connect('scroll_event', self.tracker_cor.on_scroll)

        fig.subplots_adjust(left=0.05,
                            right=0.975,
                            top=0.975,
                            bottom=0.025,
                            wspace=0.1,
                            hspace=0.075)

        # self.axes[1][1] = fig.add_subplot(224)
        super().__init__(fig)

        # self.fig = fig

        self.parent = parent

        # self.axes[0][0].plot([0, 1, 2, 3, 4], [10, 1, 20, 3, 40])

        self.cmap = plt.cm.gray
        self.index_ax = 0
        self.index_sag = 0
        self.index_cor = 0
        self.display_ax = None
        self.display_sag = None
        self.display_cor = None
        self.imshow_ax = None
        self.imshow_sag = None
        self.imshow_cor = None

    def clear(self,
              image_plane: typing.Union[image.ImagePlane, None] = None,
              # index: typing.Union[int, None] = None,
              ):
        """Clear axes, or a given axis."""
        if image_plane is not None:
            if image_plane == image.ImagePlane.AXIAL:
                self.axes[0][0].cla()
            elif image_plane == image.ImagePlane.SAGITTAL:
                self.axes[0][1].cla()
            elif image_plane == image.ImagePlane.CORONAL:
                self.axes[1][0].cla()
            # elif index == 4:
                # self.axes[1][1].cla()
            else:
                raise ValueError("Unknown image plane {image_plane}.")
        else:
            self.axes[0][0].cla()
            self.axes[0][1].cla()
            self.axes[1][0].cla()
            # self.axes[1][1].cla()

    def show(self):
        """Draw the figures."""
        # self.figure.draw()
        self.figure.canvas.draw()

    def increase_index(self,
                       change: int,
                       image_plane: image.ImagePlane,
                       ):
        """Update the displayed image index."""
        if image_plane == image.ImagePlane.AXIAL:
            self.index_ax += change
            self.index_ax = max(0,
                                min(self.index_ax, self.num_slices_ax - 1))
        elif image_plane == image.ImagePlane.SAGITTAL:
            self.index_sag += change
            self.index_sag = max(0,
                                 min(self.index_sag, self.num_slices_sag - 1))
        elif image_plane == image.ImagePlane.CORONAL:
            self.index_cor += change
            self.index_cor = max(0,
                                 min(self.index_cor, self.num_slices_cor - 1))
        else:
            raise RuntimeError("Cannot happen!")

        self.update_image()

    def set_image(self, img):
        """Update the displayed image."""
        self.image = img

        self.index_ax = img.shape[2] // 2
        self.index_sag = img.shape[1] // 2
        self.index_cor = img.shape[0] // 2

        self.display_ax = None
        self.display_sag = None
        self.display_cor = None

        self.num_slices_ax = img.shape[2]
        self.num_slices_sag = img.shape[1]
        self.num_slices_cor = img.shape[0]

        self.min_int = img.min()
        self.max_int = img.max()

        self.update_image()

    def update_image(self):
        """Draw the image."""
        img = self.image

        any_updates = False

        if self.index_ax != self.display_ax:
            self.display_ax = self.index_ax
            im = img.get_slice(self.display_ax, image.ImagePlane.AXIAL)
            im = im[::-1, :]
            if self.imshow_ax is None:
                ar = img.aspect_ratios(image.ImagePlane.AXIAL)
                # self.clear(image.ImagePlane.AXIAL)
                self.imshow_ax = self.axes[0][0].imshow(
                    im,
                    cmap=self.cmap,
                    vmin=self.min_int,
                    vmax=self.max_int,
                    )
                self.axes[0][0].invert_yaxis()
                if ar is not None:
                    self.axes[0][0].set_aspect(ar)
            else:
                self.imshow_ax.set_data(im)
            any_updates = True

        if self.index_sag != self.display_sag:
            self.display_sag = self.index_sag
            im = img.get_slice(self.display_sag, image.ImagePlane.SAGITTAL)
            im = im[::-1, :]
            if self.imshow_sag is None:
                ar = img.aspect_ratios(image.ImagePlane.SAGITTAL)
                # self.clear(image.ImagePlane.SAGITTAL)
                self.imshow_sag = self.axes[0][1].imshow(
                    im,
                    cmap=self.cmap,
                    vmin=self.min_int,
                    vmax=self.max_int,
                    )
                self.axes[0][1].invert_yaxis()
                if ar is not None:
                    self.axes[0][1].set_aspect(ar)
                # self.axes[0][1].set_xlim(self.axes[0][0].get_xlim())
                self.axes[0][1].set_ylim(self.axes[0][0].get_ylim())
            else:
                self.imshow_sag.set_data(im)
            any_updates = True

        if self.index_cor != self.display_cor:
            self.display_cor = self.index_cor
            im = img.get_slice(self.display_cor, image.ImagePlane.CORONAL)
            im = im.T
            if self.imshow_cor is None:
                ar = img.aspect_ratios(image.ImagePlane.CORONAL)
                # self.clear(image.ImagePlane.CORONAL)
                self.imshow_cor = self.axes[1][0].imshow(
                    im,
                    cmap=self.cmap,
                    vmin=self.min_int,
                    vmax=self.max_int,
                    )
                self.axes[1][0].invert_yaxis()
                if ar is not None:
                    self.axes[1][0].set_aspect(ar)
                self.axes[1][0].set_xlim(self.axes[0][0].get_xlim())
            else:
                self.imshow_cor.set_data(im)
            any_updates = True

        if any_updates:
            self.draw()


class BaseEvents():
    """Base class for GUI events."""

    def __init__(self,
                 window: QtWidgets.QMainWindow,
                 ):
        self.ui = window


class DicomTreeTools(BaseEvents):
    """Code to handle the Dicom tree."""

    def __init__(self,
                 window: QtWidgets.QMainWindow,
                 fig: MplCanvas,
                 ):
        super().__init__(window)

        self.fig = fig

        self.ui.selectDirectoryButton.clicked.connect(self.dir_button_clicked)

        self.ui.treeWidget.setHeaderLabels(["File", "Type"])
        # self.ui.treeWidget.header().setMinimumSectionSize(25)
        # TODO: Correct way? What are the units here?
        self.ui.treeWidget.header().resizeSection(1, 50)

        # self.ui.treeWidget.header().setStretchLastSection(False)
        self.ui.treeWidget.header().setSectionResizeMode(
            0, QtWidgets.QHeaderView.Stretch)
        self.ui.treeWidget.header().setSectionResizeMode(
            1, QtWidgets.QHeaderView.Fixed)

    def dir_button_clicked(self):
        """Select a directory when button clicked."""
        if not hasattr(self.ui.selectDirectoryButton, "_selected_dir"):
            # First time clicked, use user's home directory
            self.ui.selectDirectoryButton._selected_dir \
                = str(pathlib.Path.home())

        dir_ = QtWidgets.QFileDialog.getExistingDirectory(
            None,
            "Open a directory with Dicom images.",
            self.ui.selectDirectoryButton._selected_dir,
            )

        if dir_ != "":  # User did not press cancel
            path = pathlib.Path(dir_)
            if not path.is_dir():
                msgBox = QtWidgets.QMessageBox(
                    QtWidgets.QMessageBox.Critical,
                    "Error",
                    "Provided path is not a directory!",
                    QtWidgets.QMessageBox.Ok)
                msgBox.exec()
            else:
                self.ui.selectDirectoryButton._selected_dir = dir_
                self.ui.lineEdit.setText(dir_)

                self.refresh_file_tree(path)  # Update the tree view

    def tree_item_doubleclicked(self, item, column_no):
        """Event for double-clicking in tree list."""
        if item.childCount() > 0:  # Then  it is not an image.
            return

        parts = []
        while item is not None:
            parts = [item.text(0), *parts]
            item = item.parent()
        path = pathlib.Path(*parts)
        image = self.images[str(path)]

        self.fig.set_image(image)
        # print(image)
        # TODO: Plot image...

    def refresh_file_tree(self, path):
        """List all files that are Dicom files."""
        # print("List all files that are Dicom files." + str(path))
        images = dicom.find_all_dicom_files(
                    path,
                    dtype=utils.settings.dtype,
                    escalation=errors.Escalation.NOTHING,
                    verbosity=utils.settings.verbosity,
                    )
        # print(images)
        # level = 1
        # max_level = 1
        # while level <= max_level:

        name = path.parts[-1]

        # Add root folder to keys
        self.images = dict()
        for key in images:
            full_path = pathlib.Path(name, key)
            self.images[str(full_path)] = images[key]
        del images

        def _add_node(file, modality, parent):
            if len(file.parts) == 1:
                if modality is None:
                    modality = "?"
                child = QtWidgets.QTreeWidgetItem([str(file), modality])
                parent.addChild(child)
            else:
                head, rest = file.parts[0], pathlib.Path(*file.parts[1:])
                found = False
                for i in range(parent.childCount()):
                    child = parent.child(i)
                    if child.text(0) == head:
                        branch = child
                        found = True
                        break
                if not found:
                    branch = QtWidgets.QTreeWidgetItem([head])
                parent.addChild(branch)
                _add_node(rest, modality, branch)

        # Add to tree widget
        root = QtWidgets.QTreeWidgetItem([name])
        for key in self.images:
            # Remove root folder from key ...
            _add_node(pathlib.Path(*pathlib.Path(key).parts[1:]),
                      self.images[key].modality,
                      root)

        self.ui.treeWidget.insertTopLevelItems(0, [root])

        self.ui.treeWidget.itemDoubleClicked.connect(
            self.tree_item_doubleclicked)

        # self.ui.treeWidget.resizeColumnsToContents()


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    """Load and show the GUI."""

    def __init__(self, *args, obj=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        # TODO: Correct way? What are the units here?
        self.splitter.setSizes([100, 300])

        fig = MplCanvas(self, width=5, height=4, dpi=100)
        self.gridLayout_plot = QtWidgets.QGridLayout()  # self.frame)
        self.gridLayout_plot.addWidget(fig)
        self.frame.setLayout(self.gridLayout_plot)

        self.dicomTreeTools = DicomTreeTools(self, fig)


app = QtWidgets.QApplication(sys.argv)

window = MainWindow()
window.show()
app.exec_()


# import sys

# # import PySide2.QtWidgets
# # from PySide2 import QtWidgets, uic
# from PyQt5 import QtWidgets, uic

# # from ui_form import Ui_Form

# app = QtWidgets.QApplication(sys.argv)

# window = uic.loadUi("gui/main.ui")

# window.show()
# app.exec()

# class Window(PySide2.QtWidgets.QWidget):
#     """Load and show the GUI."""

#     def __init__(self, parent=None):
#         super(Window, self).__init__(parent)

#         self.m_ui = Ui_Form()
#         self.m_ui.setupUi(self)


# import sys
# from PyQt5 import QtCore, QtGui, QtWidgets
# from PyQt5 import uic


# class MainWindow(QtWidgets.QMainWindow):

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         uic.loadUi("gui/main.ui", self)


# app = QtWidgets.QApplication(sys.argv)
# window = MainWindow()
# window.show()
# app.exec_(