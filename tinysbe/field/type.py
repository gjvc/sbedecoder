#! /usr/bin/env python3

import logging
import struct

from .base import SBEMessageField
from ..aux import fmt_and_size_by_primitive_type_name, get_field_type_details

log = logging.getLogger( __name__ )


class TypeMessageField( SBEMessageField ):

    def __init__( self, constant=None, description=None, field_length=None, field_offset=None, id=None, is_string_type=False, name=None, null_value=None, optional=False, message_type_name=None, semantic_type=None, since_version=0, unpack_fmt=None ):
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
        self.message_type_name = message_type_name
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

        raw_value, = struct.unpack_from( self.unpack_fmt, self.buffer, self.field_offset )

        return raw_value


    @staticmethod
    def create( field_type_map, field_definition, field_offset, endian='<' ):

        field_type, field_schema_name, field_name, field_semantic_type, field_since_version, field_definition_type_name = get_field_type_details( field_type_map, field_definition )

        primitive_type_name = field_type[ 'primitive_type' ]
        is_string_type = primitive_type_name == 'char' and 'length' in field_type and int( field_type[ 'length' ] ) > 1
        if field_definition.get( 'offset', None ):
            field_offset = int( field_definition.get( 'offset', None ) )

        primitive_type_fmt, primitive_type_size = fmt_and_size_by_primitive_type_name[ primitive_type_name ]
        field_length = field_type.get( 'length', None )
        if field_length:
            field_length = int( field_length )
            if is_string_type:
                unpack_fmt = f'{field_length:d}s'  # unpack as string (which may be null-terminated if shorter)
            else:
                unpack_fmt = f'{endian}{field_length}{primitive_type_fmt}'
        else:
            field_length = primitive_type_size
            unpack_fmt = f'{endian}{primitive_type_fmt}'

        constant = None
        optional = False
        if 'presence' in field_type:
            if field_type[ 'presence' ] == 'constant':
                constant_prim_type = primitive_type_name
                if constant_prim_type == 'char':
                    constant = str( field_type[ 'text' ] )
                else:
                    constant = int( field_type[ 'text' ] )
            elif field_type[ 'presence' ] == 'optional':
                optional = True

        null_value = None
        if 'null_value' in field_type:
            null_value = int( field_type[ 'null_value' ] )

        field_id = field_definition.get( 'id' )
        field_description = field_definition.get( 'description', b'' )

        return TypeMessageField(
            name=field_name,
            message_type_name=field_schema_name,
            id=field_id,
            description=field_description,
            unpack_fmt=unpack_fmt,
            field_offset=field_offset,
            field_length=field_length,
            null_value=null_value,
            constant=constant,
            optional=optional,
            is_string_type=is_string_type,
            semantic_type=field_semantic_type,
            since_version=field_since_version
        )
