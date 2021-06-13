#! /usr/bin/env python3

import logging
import xml

from .aux import snake_case_from_CamelCase, fmt_and_size_by_type, field_type_name_from_field_definition, parse_type_definitions, parse_message_definitions
from .field.comp import CompositeMessageField
from .field.enum import EnumMessageField
from .field.set import SetMessageField
from .field.type import TypeMessageField
from .message import SBEMessage

log = logging.getLogger( 'tinysbe.schema' )


class SBESchema:

    def __init__( self ):
        self.field_type_map = { }
        self.message_type_map = { }
        self.message_definitions = [ ]


    def load_schema_xml_file( self, xml_filename, namespace='', uri='' ):
        log.info( f'load_schema_xml_file  {xml_filename}' )
        tree = xml.etree.ElementTree.parse( xml_filename )
        root = tree.getroot()

        self.field_type_map = parse_type_definitions( root )
        self.message_definitions = parse_message_definitions( root, namespace=namespace, uri=uri )

        for message_definition in self.message_definitions:
            self.create_message( message_definition )


    def create_message_type( self, message_definition ):

        message_name = message_definition[ 'name' ]
        message_id = int( message_definition[ 'id' ] )

        message_type = type( message_name, (SBEMessage,), { } )
        setattr( message_type, 'children', [ ] )
        setattr( message_type, 'message_id', message_id )
        setattr( message_type, 'schema_name', message_name )
        setattr( message_type, 'name', snake_case_from_CamelCase( message_name ) )

        self.message_type_map[ message_id ] = message_type

        # log_token = f'create_message_type'
        # log.info( f'{log_token:<40}  {message_name}/{message_id}' )

        return message_type


    def create_message( self, message_definition ):

        message_type = self.create_message_type( message_definition )
        self.create_header( message_type )

        fields_and_groups_list = message_definition.get( 'children', [ ] )
        self.create_fields_and_groups( 'create_fields_and_groups', message_type, fields_and_groups_list )


    def create_header( self, message_type ):

        message_header_type = self.field_type_map[ 'messageHeader' ]
        header_field_types = message_header_type.get( 'children', [ ] )

        header_size = 0
        for header_field_type in header_field_types:
            primitive_type_fmt, primitive_type_size = fmt_and_size_by_type[ header_field_type[ 'primitive_type' ] ]
            header_field_type_name = header_field_type[ 'name' ]

            message_header_field = TypeMessageField( description=f'Header {header_field_type_name}', field_length=primitive_type_size, field_offset=header_size, name=snake_case_from_CamelCase( header_field_type_name ), schema_name=header_field_type_name, unpack_fmt=primitive_type_fmt, )
            message_type.children.append( message_header_field )
            setattr( message_type, message_header_field.name, message_header_field )

            message_name_id = f'{header_size:<3}  {message_header_field.field_length:03}  {message_header_field.name}/{message_header_field.id}'
            log.info( f'{"create_header_field":<40}  {message_name_id:<40}' )

            header_size += primitive_type_size

        setattr( message_type, 'header_size', header_size )


    def create_fields_and_groups( self, log_token, message_type, fields_and_groups_list, field_offset=None ):

        if field_offset is None:
            field_offset = message_type.header_size

        for field_definition in fields_and_groups_list:

            if 'type' in field_definition:
                field = self.create_field( log_token, message_type, field_definition, field_offset )
                field_offset += field.field_length

            elif 'dimension_type' in field_definition:
                field_offset = self.create_group( log_token, message_type, field_definition, field_offset )

        return field_offset


    def create_field( self, log_token, message_type, field_definition, field_offset ):

        field_type_name = field_type_name_from_field_definition( self.field_type_map, field_definition )

        if field_type_name == 'type':
            field = TypeMessageField.create( self.field_type_map, field_definition, field_offset )

        elif field_type_name == 'enum':
            field = EnumMessageField.create( self.field_type_map, field_definition, field_offset )

        elif field_type_name == 'set':
            field = SetMessageField.create( self.field_type_map, field_definition, field_offset )

        elif field_type_name == 'composite':
            field = CompositeMessageField.create( self.field_type_map, field_definition, field_offset )

        else:
            field = None

        message_type.children.append( field )

        field_schema_name_id = f'{field_offset:<3}  {field.field_length:03}  {field.schema_name}/{field.id}'
        log.info( f'{log_token:<40}  {field_schema_name_id:<40}' )

        return field


    def create_group( self, log_token, message_type, field_definition, field_offset ):

        dimension_type_name = field_definition[ 'dimension_type' ]
        dimension_type = self.field_type_map[ dimension_type_name ]

        children = dimension_type[ 'children' ]
        field_offset = self.create_fields_and_groups( f'{log_token} *', message_type, children, field_offset )

        children = field_definition[ 'children' ]
        field_offset = self.create_fields_and_groups( f'{log_token} *', message_type, children, field_offset )

        return field_offset
