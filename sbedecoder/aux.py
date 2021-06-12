#! /usr/bin/env python3

import logging
import re

log = logging.getLogger( 'sbedecoder' )


# CamelCase <> snake_case ---------------------------------------------------------------------------

def snake_case_from_CamelCase( CamelCase ):
    interim = re.sub( r'([a-z])([A-Z]+)', r'\1_\2', CamelCase )
    interim = re.sub( r'([a-z0-9])([A-Z])', r'\1_\2', interim )
    return interim.lower()


def CamelCase_from_snake_case( snake_case ):
    return ''.join( word.title() for word in snake_case.split( '_' ) )


# ---------------------------------------------------------------------------------------------------

initial_types = {
    "char": { "children": [ ], "description": "char", "name": "char", "primitive_type": "char", "type": "type" },
    "int": { "children": [ ], "description": "int", "name": "int", "primitive_type": "int32", "type": "type" },
    "float": { "children": [ ], "description": "float", "name": "float", "primitive_type": "float", "type": "type" },
    "double": { "children": [ ], "description": "double", "name": "double", "primitive_type": "double", "type": "type" },

    "int8": { "children": [ ], "description": "int8", "name": "int8", "primitive_type": "int8", "type": "type" },
    "int16": { "children": [ ], "description": "int16", "name": "int16", "primitive_type": "int16", "type": "type" },
    "int32": { "children": [ ], "description": "int32", "name": "int32", "primitive_type": "int32", "type": "type" },
    "int64": { "children": [ ], "description": "int64", "name": "int64", "primitive_type": "int64", "type": "type" },

    "uint8": { "children": [ ], "description": "uint8", "name": "uint8", "primitive_type": "uint8", "type": "type" },
    "uint16": { "children": [ ], "description": "uint16", "name": "uint16", "primitive_type": "uint16", "type": "type" },
    "uint32": { "children": [ ], "description": "uint32", "name": "uint32", "primitive_type": "uint32", "type": "type" },
    "uint64": { "children": [ ], "description": "uint64", "name": "uint64", "primitive_type": "uint64", "type": "type" },
}

fmt_and_size_by_type = {
    'char': ('c', 1),
    'int': ('i', 4),
    'float': ('f', 4),
    'double': ('d', 8),

    'int8': ('b', 1),
    'int16': ('h', 2),
    'int32': ('i', 4),
    'int64': ('q', 8),

    'uint8': ('B', 1),
    'uint16': ('H', 2),
    'uint32': ('I', 4),
    'uint64': ('Q', 8),
}


# ---------------------------------------------------------------------------------------------------

def calculate_field_length( field_type_map, field ):
    if 'dimension_type' in field:
        type_name = field[ 'dimension_type' ]
    elif 'type' in field:
        type_name = field[ 'type' ]
    else:
        assert False

    field_type = field.get( 'primitive_type', type_name )
    fmt, size = fmt_and_size_by_type.get( field_type, (None, None) )
    if fmt and size:
        return size

    field_definition = field_type_map[ type_name ]
    encoding_type_name = field_definition.get( 'encoding_type' )
    if encoding_type_name:
        fmt, size = fmt_and_size_by_type.get( encoding_type_name, (None, None) )
        if fmt and size:
            return size

    return sum( calculate_field_length( field_type_map, child ) for child in field_definition[ 'children' ] )


def calculate_block_length( field_type_map, message ):
    if 'block_length' in message:
        return int( message[ 'block_length' ] )

    # length = 0
    # for child in message[ 'children' ]:
    #     length += child.field_length
    # return length

    return sum( calculate_field_length( field_type_map, field ) for field in message[ 'children' ] )


# ---------------------------------------------------------------------------------------------------

def dict_from_element( element ):
    d = { snake_case_from_CamelCase( name ): value for name, value in element.items() }
    d[ 'type' ] = element.tag
    if element.text:
        d[ 'text' ] = element.text.strip()
    return d


def type_definition_from_element( element ):
    type_definition = dict_from_element( element )
    type_definition[ 'children' ] = [ dict_from_element( child ) for child in list( element ) ]
    return type_definition


def name_type_definition_from_element( element ):
    type_definition = type_definition_from_element( element )
    name = type_definition[ 'name' ]
    return name, type_definition


# ---------------------------------------------------------------------------------------------------

def parse_type_definitions( root ):
    types = initial_types.copy()
    for child in list( root.find( './/types' ) ):
        new_name, new_type = name_type_definition_from_element( child )
        types[ new_name ] = new_type
    return types


# ---------------------------------------------------------------------------------------------------

def message_definition_from_element( element, definition=None ):
    if definition is None:
        definition = { snake_case_from_CamelCase( name ): value for name, value in element.items() }

    children = [ ]

    for child in list( element ):

        d = { snake_case_from_CamelCase( name ): value for name, value in child.items() }
        d[ 'converted_name' ] = snake_case_from_CamelCase( d[ 'name' ] )

        if child.tag == 'field':
            children.append( d )

        if child.tag == 'group':
            children.append( message_definition_from_element( child, definition=d ) )

    definition[ 'children' ] = children

    return definition


def parse_message_definitions( root, namespace=None, uri=None ):
    if namespace and uri:
        return [ message_definition_from_element( child ) for child in root.findall( f'.//{namespace}:message', { namespace: uri } ) ]

    return [ message_definition_from_element( child ) for child in root.findall( './/sbe:message', { 'sbe': 'http://fixprotocol.io/2016/sbe' } ) ]


# ---------------------------------------------------------------------------------------------------

def foo( field_type_map, field_definition ):

    field_schema_name = field_definition[ 'name' ]
    field_name = snake_case_from_CamelCase( field_schema_name )

    field_semantic_type = field_definition.get( 'semantic_type', None )
    field_since_version = int( field_definition.get( 'since_version', 0 ) )

    field_definition_type_name = field_definition.get( 'primitive_type', field_definition[ 'type' ] )
    field_type = field_type_map[ field_definition_type_name ]

    return field_schema_name, field_name, field_semantic_type, field_since_version, field_definition_type_name, field_type
