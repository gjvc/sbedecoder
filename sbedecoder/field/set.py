#! /usr/bin/env python3

import logging
import struct

from .base import SBEMessageField

log = logging.getLogger(__name__)


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

