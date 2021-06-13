#! /usr/bin/env python3

import argparse
import logging
import os
import pathlib
import sys
import time

import tinysbe.schema
import parse


# -----------------------------------------------------------------------------

logging.basicConfig( datefmt='%Y-%m-%dT%H:%M:%S%z', format='{asctime}  {process:<5}  {levelname:<5}  {filename}:{lineno:<3}  {message}', style='{' )
logging.getLogger().setLevel( logging.INFO )
logging.getLogger( 'tinysbe' ).setLevel( logging.INFO )
logging.getLogger( 'tinysbe.schema' ).setLevel( logging.DEBUG )
logging.Formatter.converter = time.gmtime

# -----------------------------------------------------------------------------

log = logging.getLogger()

PROJECT_ROOT = pathlib.Path( __file__ ).parents[ 4 ]


# -----------------------------------------------------------------------------

def filename_source( dirname ):
    for basename in pathlib.Path( dirname ).iterdir():
        yield dirname / basename


def message_source( dirname ):
    for filename in filename_source( dirname ):
        with open( filename, 'rb' ) as stream:
            yield filename, stream.read()


def sorted_message_source( dirname, reverse=True ):
    for filename in sorted( list( filename_source( dirname ) ), key=lambda filename: os.stat( filename ).st_size, reverse=reverse ):
        with open( filename, 'rb' ) as stream:
            yield filename, stream.read()


# -----------------------------------------------------------------------------

def mfsbe_schema_xml_filename( mfsbe_schema_version=18654 ):
    return PROJECT_ROOT / f'res/fix/mfsbe4-{mfsbe_schema_version}.xml'


def process_directory( message_factory, source_directory ):
    failures = 0
    n = 0
    for filename, message in list( sorted_message_source( source_directory ) ):
        n += 1
        try:
            process_single_file( message_factory, filename, message )
        except Exception as e:
            log.error( f'{filename}  {e}' )
            failures += 1
    log.info( f'complete: processed {n} files, {failures} failures' )


def process_single_file( message_factory, output_log_file, input_sbe_file ):
    with open( input_sbe_file, 'rb' ) as stream:
        contents = stream.read()
        m, bytes_decoded = message_factory.build( contents )
        for field in m.children:
            message_name_id = f'{m.name}/{m.message_id}'
            log.info( f'{field.field_offset:03}  {field.field_length:03}  {message_name_id:<32}  {field.schema_name:<32}  {field.value}' )


def execute( options ):
    schema = tinysbe.schema.SBESchema()
    schema.load( options.schema_xml_filename, namespace='sbe', uri='http://fixprotocol.io/2016/sbe' )
    message_factory = parse.MFSBEMessageFactory( schema )

    if options.directory:
        return process_directory( message_factory, options.directory )

    if options.input_sbe_file and options.output_log_file:
        return process_single_file( message_factory, options.output_log_file, options.input_sbe_file )


# -----------------------------------------------------------------------------

def main():
    schema_xml_filename = mfsbe_schema_xml_filename()

    parser = argparse.ArgumentParser()
    parser.add_argument( '--schema-xml-filename', default=schema_xml_filename )
    parser.add_argument( '--directory' )
    parser.add_argument( '--input-sbe-file' )
    parser.add_argument( '--output-log-file' )
    args = parser.parse_args()
    execute( args )


# -----------------------------------------------------------------------------

if __name__ == '__main__':
    sys.exit( main() )
