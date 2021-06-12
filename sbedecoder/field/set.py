#! /usr/bin/env python3

import logging
import struct

from .base import SBEMessageField
from ..aux import fmt_and_size_by_type

log = logging.getLogger( __name__ )


class SetMessageField( SBEMessageField ):

    def __init__( self, choices=None, description=None, field_length=None, field_offset=None, id=None, name=None, schema_name=None, semantic_type=None, since_version=0, unpack_fmt=None ):
        super().__init__()
        self.choices = choices
        self.description = description
        self.field_length = field_length
        self.field_offset = field_offset
        self.id = id
        self.name = name
        self.schema_name = schema_name
        self.semantic_type = semantic_type
        self.since_version = since_version
        self.name_by_text = { int( x[ 'text' ] ): x[ 'name' ] for x in choices }
        self.unpack_fmt = unpack_fmt


    @property
    def raw_value( self ):
        _raw_value, = struct.unpack_from( self.unpack_fmt, self.buffer, self.field_offset )
        return _raw_value


    @property
    def value( self ):
        _raw_value, _value = self.raw_value, 0
        _num_values = 0

        _a = [ ]
        for i in range( self.field_length * 8 ):
            bit_set = 1 & (_raw_value >> i)
            if bit_set:
                if _num_values > 0:
                    _a.append( _value )
                    _a.append( i )

        return ', '.join( _a )


    @staticmethod
    def create( field_type_map, field_definition, field_name, field_schema_name, field_semantic_type, field_since_version, field_type, offset, endian='<' ):
        field_offset = offset
        if field_definition.get( 'offset', None ):
            field_offset = int( field_definition.get( 'offset', None ) )

        encoding_type = field_type[ 'encoding_type' ]
        encoding_type_type = field_type_map[ encoding_type ]

        type_ = encoding_type_type[ 'primitive_type' ]
        primitive_type_fmt, primitive_type_size = fmt_and_size_by_type[ type_ ]

        field_length = field_type.get( 'length', None )
        if field_length:
            field_length = int( field_length )
            unpack_fmt = f'{endian}{field_length * primitive_type_fmt}'
        else:
            field_length = primitive_type_size
            unpack_fmt = f'{endian}{primitive_type_fmt}'

        choice_values = field_type[ 'children' ]
        field_id = field_definition[ 'id' ]
        field_description = field_definition.get( 'description', b'' )

        return SetMessageField( choices=choice_values, description=field_description, field_length=field_length, field_offset=field_offset, id=field_id, name=field_name, schema_name=field_schema_name, semantic_type=field_semantic_type, since_version=field_since_version, unpack_fmt=unpack_fmt, )
