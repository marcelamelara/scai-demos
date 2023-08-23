#!/bin/bash

# Copyright 2023 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

VENV_DIR="${VENVDIR:=../../scai-venv}"
EXAMPLE_DIR=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

# -----------------------------------------------------------------
# Run SBOM and SLSA evidence collection example
# -----------------------------------------------------------------

mkdir -p ${EXAMPLE_DIR}/metadata

source ${VENV_DIR}/bin/activate

SBOM_URL="https://github.com/marcelamelara/private-data-objects/suites/14743599027/artifacts/838001247"

PROVENANCE_URL="https://github.com/marcelamelara/private-data-objects/suites/14743599027/artifacts/838001246"

echo GENERATE PDO CLIENT CONTAINER SBOM DESCRIPTOR

scai-gen-resource-desc -d -f pdo_client_wawaka.spdx.json -l ${SBOM_URL} -t application/spdx+json --resource-dir ${EXAMPLE_DIR}/metadata -o sbom-desc.json --out-dir ${EXAMPLE_DIR}/metadata

echo GENERATE PDO CLIENT CONTAINER SLSA PROVENANCE DESCRIPTOR

scai-gen-resource-desc -d -f pdo_client_wawaka.slsa.intoto.jsonl -l ${PROVENANCE_URL} -t application/x.dsse+jsonl --resource-dir ${EXAMPLE_DIR}/metadata -o slsa-desc.json --out-dir ${EXAMPLE_DIR}/metadata

echo GENERATE HAS-SBOM SCAI ATTRIBUTE ASSERTION

scai-attr-assertion -a "HasSBOM" -e ${EXAMPLE_DIR}/metadata/sbom-desc.json -o has-sbom-assertion.json --out-dir ${EXAMPLE_DIR}/metadata --pretty-print

echo GENERATE HAS-SLSA SCAI ATTRIBUTE ASSERTION

scai-attr-assertion -a "HasSLSA" -e ${EXAMPLE_DIR}/metadata/slsa-desc.json -o has-slsa-assertion.json --out-dir ${EXAMPLE_DIR}/metadata --pretty-print

echo GENERATE SCAI REPORT FOR CONTAINER EVIDENCE COLLECTION

scai-report -s container-img-desc.json --subject-dirs ${EXAMPLE_DIR}/metadata -a has-sbom-assertion.json has-slsa-assertion.json --assertion-dir ${EXAMPLE_DIR}/metadata -o evidence-collection.scai.json --out-dir ${EXAMPLE_DIR}/metadata --pretty-print
