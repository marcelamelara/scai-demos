#!/usr/bin/env python3
# Copyright 2023 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
<Program Name>
  scai-report

<Author>
 Marcela Melara <marcela.melara@intel.com>

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Command-line interface for generating ITE-9 SCAI Attribute Reports.
"""

import argparse
import json
import os
import sys

from scai_generator.utility import load_json_file
from in_toto_attestation.predicates.scai.v0.scai import AttributeReport, SCAI_PREDICATE_TYPE, SCAI_PREDICATE_VERSION
import in_toto_attestation.predicates.scai.v0.scai_pb2 as scaipb
import in_toto_attestation.v1.resource_descriptor_pb2 as rdpb
from in_toto_attestation.v1.statement import Statement

import google.protobuf.json_format as pb_json

def Main():
    parser = argparse.ArgumentParser(allow_abbrev=False)

    parser.add_argument('-s', '--subjects', help='Filenames of JSON-encoded subject resource descriptors', nargs='+', type=str, required=True)
    parser.add_argument('-a', '--attribute-assertions', help='Filenames of JSON-encoded SCAI attribute assertions', nargs='+', type=str, required=True)
    parser.add_argument('-p', '--producer', help='Filename of JSON-encoded producer resource descriptor', type=str)
    parser.add_argument('-o', '--outfile', help='Filename to write out this SCAI attribute report', type=str, required=True)
    parser.add_argument('--subject-dirs', help='Directories for searching subject artifact descriptors', nargs='+', type=str)
    parser.add_argument('--assertion-dir', help='Directory for searching assertion files', type=str, default='.')
    parser.add_argument('--producer-dir', help='Directory for searching producer descriptors', type=str, default='.')
    parser.add_argument('--out-dir', help='Directory for storing generated files', type=str, default='.')
    parser.add_argument('--pretty-print', help='Flag to pretty-print all json before storing', action='store_true')
    
    options = parser.parse_args()
    
    print('Generating SCAI Attribute Report for subjects: {0}'.format(str(options.subjects)))

    # check all possible subject directories
    subjects_dir = ['.']
    subjects_dir.extend(options.subject_dirs)

    subject_list = []
    for s in options.subjects:
        for d in subjects_dir:
            try:
                sdict = load_json_file(s, search_path=d)
            except FileNotFoundError:
                continue

            subject_pb = pb_json.ParseDict(sdict, rdpb.ResourceDescriptor())
            subject_list.append(subject_pb)
            break

    # assume all SCAI assertions are in the same location
    assertions = []
    for a in options.attribute_assertions:
        adict = load_json_file(a, search_path=options.assertion_dir)
        assertion_pb = pb_json.ParseDict(adict, scaipb.AttributeAssertion())
        assertions.append(assertion_pb)
        
    # Load the producer descriptor
    producer_pb = None
    if options.producer:
        pdict = load_json_file(options.producer, options.producer_dir)
        producer_pb = pb_json.ParseDict(pdict, rdpb.ResourceDescriptor())
    
    report = AttributeReport(assertions, producer=producer_pb)

    # validate the report format, including assertions and RDs
    try:
        report.validate() 
    except ValueError as e:
        sys.exit(e)

    # Write the SCAI AttributeReport as an in-toto Statement
    scai_pred_type = SCAI_PREDICATE_TYPE+SCAI_PREDICATE_VERSION
    scai_pred_dict = pb_json.MessageToDict(report.pb)
    statement = Statement(subject_list, scai_pred_type, scai_pred_dict)

    # validate the statement format, including the subjects
    # NOTE: this does not validate the predicate itself
    try:
        statement.validate() 
    except ValueError as e:
        sys.exit(e)

    # Write out the statement file
    outfile = options.outfile
    if not outfile.endswith('.json'):
        outfile += '.json'

    indent = 0
    if options.pretty_print:
        indent = 4

    stmt_file = os.path.join(options.out_dir, outfile)
    with open(stmt_file, 'w+') as f :
        f.write(pb_json.MessageToJson(statement.pb, indent=indent))

    print('Wrote in-toto SCAI report: {0}'.format(stmt_file))

if __name__ == "__main__":
    Main()
