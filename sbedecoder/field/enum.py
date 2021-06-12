#! /usr/bin/env python3

import logging
import struct

from .base import SBEMessageField
from ..aux import fmt_and_size_by_type, foo

log = logging.getLogger( __name__ )


class EnumMessageField( SBEMessageField ):

    def __init__( self, description=None, enum_values=None, field_length=None, field_offset=None, id=None, name=None, schema_name=None, semantic_type=None, since_version=0, unpack_fmt=None ):
        super().__init__()
        self.description = description
        self.enum_values = enum_values
        self.field_length = field_length
        self.field_offset = field_offset
        self.id = id
        self.name = name
        self.schema_name = schema_name
        self.semantic_type = semantic_type
        self.since_version = since_version
        self.description_by_enum_text = { x[ 'text' ]: x.get( 'description', '' ) for x in enum_values }
        self.name_by_enum_text = { x[ 'text' ]: x[ 'name' ] for x in enum_values }
        self.unpack_fmt = unpack_fmt


    @property
    def value( self ):
        _raw_value = self.raw_value
        return _raw_value
        # _value = self.description_by_enum_text.get( str( _raw_value ), None )
        # return _value


    @property
    def enumerant( self ):
        _raw_value = self.raw_value
        _enumerant = self.name_by_enum_text.get( str( _raw_value ), None )
        return _enumerant


    @property
    def raw_value( self ):
        if self.buffer is None:
            return b''
        assert self.buffer is not None
        assert self.offset is not None
        _raw_value, = struct.unpack_from( self.unpack_fmt, self.buffer, self.field_offset )
        if type( _raw_value ) is bytes:
            _raw_value = _raw_value.decode( 'UTF-8' )
        return _raw_value


    @staticmethod
    def create( field_type_map, field_definition, field_offset, endian='<' ):

        field_schema_name, field_name, field_semantic_type, field_since_version, field_definition_type_name, field_type = foo( field_type_map, field_definition )

        encoding_type = field_type[ 'encoding_type' ]
        encoding_type_type = field_type_map[ encoding_type ]

        primitive_type_ = encoding_type_type[ 'primitive_type' ]
        primitive_type_fmt, primitive_type_size = fmt_and_size_by_type[ primitive_type_ ]

        if field_definition.get( 'offset', None ):
            field_offset = int( field_definition.get( 'offset', None ) )

        field_length = field_type.get( 'length', None )
        if field_length:
            field_length = int( field_length )
            unpack_fmt = f'{endian}{field_length * primitive_type_fmt}'
        else:
            field_length = primitive_type_size
            unpack_fmt = f'{endian}{primitive_type_fmt}'

        enum_values = field_type[ 'children' ]
        field_id = field_definition[ 'id' ]
        field_description = field_definition.get( 'description', b'' )

        return EnumMessageField( description=field_description, enum_values=enum_values, field_length=field_length, field_offset=field_offset, id=field_id, name=field_name, schema_name=field_schema_name, semantic_type=field_semantic_type, since_version=field_since_version, unpack_fmt=unpack_fmt, )
