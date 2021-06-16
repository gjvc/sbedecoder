#! /usr/bin/env python3

import logging
import struct

from .base import SBEMessageField
from ..aux import fmt_and_size_by_primitive_type_name, get_field_type_details

log = logging.getLogger( __name__ )


class EnumMessageField( SBEMessageField ):

    def __init__( self, description=None, enum_values=None, field_length=None, field_offset=None, id=None, name=None, message_type_name=None, semantic_type=None, since_version=0, unpack_fmt=None ):
        super().__init__()
        self.description = description
        self.enum_values = enum_values
        self.field_length = field_length
        self.field_offset = field_offset
        self.id = id
        self.name = name
        self.message_type_name = message_type_name
        self.semantic_type = semantic_type
        self.since_version = since_version
        self.description_by_enum_text = { x[ 'text' ]: x.get( 'description', '' ) for x in enum_values }
        self.name_by_enum_text = { x[ 'text' ]: x[ 'name' ] for x in enum_values }
        self.unpack_fmt = unpack_fmt


    @property
    def value( self ):
        return self.raw_value
        # value = self.description_by_enum_text.get( str( self.raw_value ), None )
        # return value


    @property
    def enumerant( self ):
        return self.name_by_enum_text.get( str( self.raw_value ), None )


    @property
    def raw_value( self ):
        if self.buffer is None:
            return b''
        assert self.buffer is not None
        assert self.offset is not None
        raw_value, = struct.unpack_from( self.unpack_fmt, self.buffer, self.field_offset )
        if type( raw_value ) is bytes:
            raw_value = raw_value.decode( 'UTF-8' )
        return raw_value


    @staticmethod
    def create( field_type_map, field_definition, field_offset, endian='<' ):

        field_type, field_schema_name, field_name, field_semantic_type, field_since_version, field_definition_type_name = get_field_type_details( field_type_map, field_definition )

        encoding_type = field_type[ 'encoding_type' ]
        encoding_type_type = field_type_map[ encoding_type ]

        primitive_type_name = encoding_type_type[ 'primitive_type' ]
        primitive_type_fmt, primitive_type_size = fmt_and_size_by_primitive_type_name[ primitive_type_name ]

        if field_definition.get( 'offset', None ):
            field_offset = int( field_definition.get( 'offset', None ) )

        field_length = field_type.get( 'length', None )
        if field_length:
            unpack_fmt = f'{endian}{field_length * primitive_type_fmt}'
        else:
            field_length = primitive_type_size
            unpack_fmt = f'{endian}{primitive_type_fmt}'

        enum_values = field_type[ 'children' ]
        field_id = field_definition[ 'id' ]
        field_description = field_definition.get( 'description', b'' )

        return EnumMessageField( description=field_description, enum_values=enum_values, field_length=field_length, field_offset=field_offset, id=field_id, name=field_name, message_type_name=field_schema_name, semantic_type=field_semantic_type, since_version=field_since_version, unpack_fmt=unpack_fmt, )
