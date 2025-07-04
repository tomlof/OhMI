#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A general tree class (`Node`) and helper functions.

Created on Wed Jan 15 09:39:44 2025

Copyright (c) 2025, Tommy Löfstedt. All rights reserved.

@author:  Tommy Löfstedt
@email:   tommy.lofstedt@umu.se
@license: BSD 3-clause.
"""
import os
import abc
import typing
import collections

import errors


__all__ = ["TreePrintStyleBase", "TreePrintStyleASCII",
           "TreePrintStyleUnicode",
           "Node",
           "BaseIterator", "BFSIterator", "DFSIterator",
           "find_all", "find_first",
           ]


class TreePrintStyleBase(metaclass=abc.ABCMeta):
    """Base class for tree print styles."""

    def __init__(self,
                 vertical,  # : str,
                 branch,  # : str,
                 end,  # : str,
                 blank,  # : str,
                 ):
        super().__init__()

        self.vertical = vertical
        self.branch = branch
        self.end = end
        self.blank = blank


class TreePrintStyleASCII(TreePrintStyleBase):
    """A simple ASCII style for printing trees."""

    def __init__(self):
        super().__init__(
            vertical="|   ",  # : str,
            branch="|-- ",  # : str,
            end="+-- ",  # : str,
            blank="    ",  # : str,
        )


class TreePrintStyleUnicode(TreePrintStyleBase):
    """A Unicode style for printing trees."""

    def __init__(self):
        super().__init__(
            vertical="\u2502   ",
            branch="\u251c\u2500\u2500 ",
            end="\u2514\u2500\u2500 ",
            blank="    ",  # : str,
        )


class Node(object):
    """Create node in a tree."""

    def __init__(self,
                 label,  # : str,
                 data=None,  # : object,
                 *,  # Parent must be a key-word argument
                 parent=None,  # : typing.Union[Node, None] = None,
                 ):
        self.label = str(label)
        self.data = data

        if parent is None or isinstance(parent, Node):
            self.parent = parent
        else:
            raise ValueError("The `parent` must be of type `Node`.")

        self.children = []

    @property
    def parent(self):
        """Property field parent."""
        return self._parent

    @parent.setter
    def parent(self, value):
        """Setter for property field parent."""
        if value is None or isinstance(value, Node):
            self._parent = value
        else:
            raise ValueError("The provided parent must be either `None` or "
                             "`Node`.")
        if self._parent is not None:
            self._parent.children.append(self)

    def render(self,
               style: TreePrintStyleBase = TreePrintStyleUnicode(),
               linesep: str = os.linesep,
               ):
        """Create a string with the entire tree."""
        _strs = [self.label]

        def _print(node,  # : Node,
                   prefix="",  # :
                   ):

            for i, child in enumerate(node.children):
                if i < len(node.children) - 1:  # Before the last children
                    _strs.append(prefix + style.branch + child.label)
                    _print(child, prefix + style.vertical)
                else:  # Last child
                    _strs.append(prefix + style.end + child.label)
                    _print(child, prefix + style.blank)

        _print(self)  # , prefix="> ")

        return linesep.join(_strs)

    def __repr__(self,  # : Node,
                 ):
        """Create a string representation of the Node object."""
        return str(self)

    def __str__(self,  # : Node,
                ):
        """Create a string representation of the Node object."""
        return f"{self.__class__.__name__}(" + \
            f"{self.label}, " + \
            f"{self.data}, " + \
            f"{self.parent})"

    # def to_string(self,  # : Node,
    #               levels=None,  # typing.Union[int, Node],
    #               ):
    #     if self.parent is None:
    #         return f"{self.__class__.__name__}(" + \
    #             f"{self.label}, " + \
    #             f"{self.data}, " + \
    #             f"{self.parent})"
    #     else:
    #         # TODO


class BaseIterator(metaclass=abc.ABCMeta):
    """Base class for tree iterators."""

    def __init__(self, node):
        super().__init__()

        self.node = node


class BFSIterator(BaseIterator):
    """Iterate through a tree in breath-first order."""

    def __init__(self, node):
        super().__init__(node)

    def __iter__(self):  # : Node):
        """Create an iterator over the tree."""
        queue = [self.node]
        while len(queue) > 0:
            node = queue.pop(0)  # Remove and return _first_ element from queue

            yield node  # Let the user process this node

            for child in node.children:  # Then expand and add children
                queue.append(child)


class DFSIterator(BaseIterator):
    """Iterate through a tree in depth-first order."""

    def __init__(self, node):
        super().__init__(node)

    def __iter__(self):  # : Node):
        """Create an iterator over the tree."""
        stack = [self.node]
        while len(stack) > 0:
            node = stack.pop()  # Remove and return _last_ element from stack

            yield node  # Let the user process this node

            # Then expand and add children
            # Add in reverse order to start with the first one
            for child in reversed(node.children):
                stack.append(child)


def find_all(node: Node,
             filter_: collections.abc.Callable[[Node], bool],
             *,
             iterator: type[BaseIterator] = BFSIterator,
             ):
    """Find all nodes that match the `filter_`."""
    nodes = []
    for node_ in iterator(node):
        if filter_(node_):
            nodes.append(node_)

    return nodes


def find_first(node: Node,
               filter_: collections.abc.Callable[[Node], bool],
               *,
               iterator: type[BaseIterator] = BFSIterator,
               ):
    """Find the first node that matches the `filter_`."""
    for node_ in iterator(node):
        if filter_(node_):
            return node_

    raise errors.NotFoundError("No node found matching the filter.")


class BaseFilter(collections.abc.Callable, metaclass=abc.ABCMeta):
    pass


class SimpleFilter(BaseFilter):
    def __init__(self: BaseFilter,
                 filter_: collections.abc.Callable[[Node], bool],
                 ) -> BaseFilter:
        if isinstance(filter_, collections.Callable):
            self.filter_ = filter_
        else:
            raise ValueError("The provided `filter_` must be callable.")

    def __call__(self: BaseFilter,
                 node: Node,
                 ):
        return self.filter_(node)
