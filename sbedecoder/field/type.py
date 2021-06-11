#! /usr/bin/env python3

import logging
import struct

from .base import SBEMessageField

log = logging.getLogger(__name__)


class TypeMessageField( SBEMessageField ):

    def __init__( self, constant=None, description=None, field_length=None, field_offset=None, id=None, is_string_type=False, name=None, null_value=None, optional=False, schema_name=None, semantic_type=None, since_version=0, unpack_fmt=None ):
        super().__init__()
        self.constant = constant
        self.description = description
        self.field_length = field_length
        self.field_offset = field_offset
        self.id = id
        self.is_string_type = is_string_type
        self.name = name
        self.null_value = null_value
        self.optional = optional
        self.schema_name = schema_name
        self.semantic_type = semantic_type
        self.since_version = since_version
        self.unpack_fmt = unpack_fmt


    @property
    def value( self ):

        if self.null_value:
            if self.raw_value == self.null_value:
                return ''

        if self.is_string_type:
            parts = self.raw_value.split( b'\0', 1 )
            return parts[ 0 ].decode( 'utf-8' )

        return self.raw_value


    @property
    def raw_value( self ):
        if self.constant is not None:
            return self.constant

        if self.buffer is None:
            return b''

        _raw_value, = struct.unpack_from( self.unpack_fmt, self.buffer, self.field_offset )

        return _raw_value
