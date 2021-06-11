#! /usr/bin/env python3

import logging
import math

from .base import SBEMessageField

log = logging.getLogger( __name__ )


class CompositeMessageField( SBEMessageField ):

    def __init__( self, description=None, field_length=None, field_offset=None, float_value=False, id=None, name=None, schema_name=None, parts=None, semantic_type=None, since_version=0 ):
        super().__init__()
        self.description = description
        self.field_length = field_length
        self.field_offset = field_offset
        self.float_value = float_value
        self.id = id
        self.name = name
        self.schema_name = schema_name
        self.parts = parts
        self.semantic_type = semantic_type
        self.since_version = since_version

        for part in self.parts:
            setattr( self, part.name, part )


    def wrap( self, buffer, offset, relative_offset=0 ):
        # log.info( f'{"wrap":<40} {offset:03}  {self.field_offset:4}   {self.field_length:4}' )
        self.buffer, self.offset = buffer, offset
        relative_offset = 0
        for part in self.parts:
            schema_name_id = f'{self.schema_name}/{self.id}'
            log.info( f'{"composite-field-wrap":<40}  {offset:03}  {part.field_length:02x}  {schema_name_id:<40}  {part.name}  {self.name} (offset in composite_field {relative_offset})' )
            relative_offset += part.field_length
            part.wrap( buffer, offset )


    @property
    def value( self ):

        if self.float_value:
            mantissa, exponent = self.raw_value.get( 'mantissa', None ), self.raw_value.get( 'exponent', None )
            if mantissa in (None, b'', ''):
                mantissa = 0
            if exponent in (None, b'', ''):
                exponent = 0
            return float( mantissa ) * math.pow( 10, exponent )

        return self.raw_value


    @property
    def raw_value( self ):
        return { p.name: p.value for p in self.parts }
