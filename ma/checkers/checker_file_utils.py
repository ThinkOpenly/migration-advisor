# -*- coding: utf-8 -*-

"""
Copyright (C) 2017 IBM Corporation

Licensed under the Apache License, Version 2.0 (the “License”);
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an “AS IS” BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

    Contributors:
        * Roberto Oliveira <rdutra@br.ibm.com>
        * Diego Fernandez-Merjildo <merjildo@br.ibm.com>
"""

import re
from ma import core

LINE_DELIMITER = "$"


def get_all_statements(names, file_name):
    """ Get all statements from a file that contains specific names. The
    parameter 'names' is a list of names that will be searched in the file.
    This function returns a list with the line number and the statement, e.g:
        <line_number>:<statement>
     """
    # Run grep command to get lines that contain searched names
    grep_delimiter = "\|"
    command = "grep -n '"
    for name in names:
        command += name + grep_delimiter
    command = command[:-len(grep_delimiter)]
    command += "' " + file_name + " | cut -f1 -d:"
    lines = core.execute_stdout(command)[1]

    # Run awk command to get entire statements from problematic lines
    awk_delimiter = '||'
    command = "awk '"
    for line in lines.split():
        command += "NR==" + line + awk_delimiter
    command = command[:-len(awk_delimiter)]
    command += ",/;/ {print NR\"" + LINE_DELIMITER + "\", $0}' " + file_name
    output = core.execute_stdout(command)[1]

    # Parse the output and join lines that are part of the same statement
    statements = []
    statement = ''
    for out in output.strip().split("\n"):
        if ";" in out:
            if "\n" in statement:
                statement += out.split(LINE_DELIMITER)[1]
            else:
                statement += out
            statements.append(statement)
            statement = ''
        else:
            statement += out + "\n"
    return statements


def format_statements(statements, names):
    """ Format statements by the minimum size make it valid and return a list
    of lists, in which each list contains the line number and the minimum valid
    statement

    The parameter 'statements' is a list of statements to be formatted and
    should be in format: <line_number>:<statement>
    The parameter 'names' is a list of names used to format the statement and
    get the minimum valid statement.

    Formatting e.g:
        parameter 'names' contains "int"
        code:       int x = 10;
        formatting: int x

        parameter 'names' contains "sum"
        code:       int x = sum(y, z);
        formatting: sum(y, z)
    """
    formatted_statements = []
    for report in statements:
        if LINE_DELIMITER not in report:
            return formatted_statements
        line = int(report.split(LINE_DELIMITER)[0])
        content = report.split(LINE_DELIMITER)[1].strip()

        # Split statement and keep the delimiters
        tokens = re.split('(\(| |=|;|\\t)', content)
        for index, token in enumerate(tokens):
            if token == "\n":
                line += 1
            if token not in names:
                continue
            # Mount the statement
            while "=" not in token and ";" not in token:
                index += 1
                token += tokens[index]
            statement = token[:-1]
            formatted_statements.append([statement, line])
    return formatted_statements
