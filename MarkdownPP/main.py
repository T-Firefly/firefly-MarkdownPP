#!/usr/bin/env python

# Copyright (C) 2010 John Reese
# Licensed under the MIT license

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import sys
import MarkdownPP
import json

import os
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from jinja2 import *


# Terminal output ANSI color codes
class colors:
    BLUE = '\033[36;49;22m'
    MAGB = '\033[35;49;1m'
    GREEN = '\033[32;49;22m'
    NORMAL = '\033[0m'


# Custom event handler for watchdog observer
class MarkdownPPFileEventHandler(PatternMatchingEventHandler):
    # Look for .mdpp files
    patterns = ["*.mdpp"]

    def process(self, event):
        modules = MarkdownPP.modules.keys()
        mdpp = open(event.src_path, 'r')

        # Output file takes filename from input file but has .md extension
        md = open(os.path.splitext(event.src_path)[0]+'.md', 'w')
        MarkdownPP.MarkdownPP(input=mdpp, output=md, modules=modules)

        # Logs time and file changed (with colors!)
        print(time.strftime("%c") + ":",
              colors.MAGB + event.src_path,
              colors.GREEN + event.event_type,
              "and processed with MarkdownPP",
              colors.NORMAL)

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)


def main():
    # setup command line arguments
    parser = argparse.ArgumentParser(description='Preprocessor for Markdown'
                                     ' files.')

    parser.add_argument('FILENAME', help='Input file name (or directory if '
                        'watching)')

    # Argument for watching directory and subdirectory to process .mdpp files
    parser.add_argument('-w', '--watch', action='store_true', help='Watch '
                        'current directory and subdirectories for changing '
                        '.mdpp files and process in local directory. File '
                        'output name is same as file input name.')

    parser.add_argument('-o', '--output', help='Output file name. If no '
                        'output file is specified, writes output to stdout.')
    parser.add_argument('-e', '--exclude', help='List of modules to '
                        'exclude, separated by commas. Available modules: '
                        + ', '.join(MarkdownPP.modules.keys()))

    parser.add_argument('-f', '--file', action='append', help='Json file name, '
                        'to load the environment args. ')

    parser.add_argument('-E', '--env', help='Indicate environmental variables. '
                        'Can overwrite the variables in Json. Variables are '
                        'separated by spaces. '
                        'Example: -E "name=zhangsan args=10". ')

    parser.add_argument('-I', '--include', action='append', help='Indicate the '
                        'path of .mdpp file. Can indicate multiple path, and the'
                        'first path has the highest priority.'
                        'Example: -I "file1/path1" -I "file2/path2"')

    args = parser.parse_args()

    # If watch flag is on, watch dirs instead of processing individual file
    if args.watch:
        # Get full directory path to print
        p = os.path.abspath(args.FILENAME)
        print("Watching: " + p + " (and subdirectories)")

        # Custom watchdog event handler specific for .mdpp files
        event_handler = MarkdownPPFileEventHandler()
        observer = Observer()
        # pass event handler, directory, and flag to recurse subdirectories
        observer.schedule(event_handler, args.FILENAME, recursive=True)
        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    else:
        mdpp = open(args.FILENAME, 'r')
        if args.output:
            md = open(args.output, 'w')
        else:
            md = sys.stdout

        env_dict = {}
        if args.file:
            for files in args.file:
                env_f = open(files, 'r')
                env_dict.update(json.load(env_f))
                env_f.close()

        if args.env:
            list_env = args.env.split(' ')
            for i in list_env:
                env_dict[i.split('=')[0]] = i.split('=')[1]

        if args.include:
            path = args.include
        else:
            path = []

        modules = list(MarkdownPP.modules)

        if args.exclude:
            for module in args.exclude.split(','):
                if module in modules:
                    modules.remove(module)
                else:
                    print('Cannot exclude ', module, ' - no such module')

        #1.先将.mdpp文件用jinja2渲染后的内容存到到临时文件temp中
        # if md != sys.stdout:
        #     Env = Environment(loader = FileSystemLoader(searchpath="./"), undefined=StrictUndefined)
        #     template = Env.get_template(args.FILENAME)
        #     temp = open("temp", 'w')
        #     temp.write(template.render(env_dict))
        #     temp.close()
        #     mdpp.close()
        #     mdpp = open("temp", 'r')

        # #2.将temp文件用MarkdownPP生成.md文件
        # MarkdownPP.MarkdownPP(input=mdpp, output=md, modules=modules, path=path)
        # md.close()
        # mdpp.close()

        # #3.将.md文件再用jinja2渲染一次
        # if md != sys.stdout:
        #     Env = Environment(loader = FileSystemLoader(searchpath="./"), undefined=StrictUndefined)
        #     template = Env.get_template(args.output)
        #     md = open(args.output, 'w')
        #     md.write(template.render(env_dict))
        #     md.close()

        #1.先将.mdpp文件用jinja2渲染后的内容存到到临时文件temp中
        if md != sys.stdout:
            Env = Environment(loader = FileSystemLoader(searchpath="./"), undefined=StrictUndefined)
            template = Env.get_template(args.FILENAME)
            temp = open("temp", 'w')
            temp.write(template.render(env_dict))
            temp.close()
            mdpp.close()
            mdpp = open("temp", 'r')

        #2.将temp文件用MarkdownPP生成.md文件
        MarkdownPP.MarkdownPP(input=mdpp, output=md, modules=modules, path=path)
        md.close()
        mdpp.close()

        #3.将.md文件再用jinja2渲染一次
        if md != sys.stdout:
            Env = Environment(loader = FileSystemLoader(searchpath="./"), undefined=StrictUndefined)
            template = Env.get_template(args.output)
            temp = open("temp", 'w')
            temp.write(template.render(env_dict))
            temp.close()
            mdpp.close()
            mdpp = open("temp", 'r')

        #4.将temp文件用MarkdownPP生成.md文件
        MarkdownPP.MarkdownPP(input=mdpp, output=md, modules=modules, path=path)
        md.close()
        mdpp.close()

        #5.将.md文件再用jinja2渲染一次
        if md != sys.stdout:
            Env = Environment(loader = FileSystemLoader(searchpath="./"), undefined=StrictUndefined)
            template = Env.get_template(args.output)
            md = open(args.output, 'w')
            md.write(template.render(env_dict))
            md.close()

#        mdpp.close()

if __name__ == "__main__":
    main()


