#! /usr/bin/env python3

import logging
import math

from .base import SBEMessageField
from .type import TypeMessageField
from ..aux import fmt_and_size_by_type, get_field_type_details

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


    def wrap( self, buffer, offset ):
        # log.info( f'{"wrap":<40} {offset:03}  {self.field_offset:4}   {self.field_length:4}' )
        self.buffer, self.offset = buffer, offset
        relative_offset = 0
        for part in self.parts:
            schema_name_id = f'{self.schema_name}/{self.id}'
            # log.info( f'{"composite-field-wrap":<40}  {offset:03}  {part.field_length:02x}  {schema_name_id:<40}  {part.name}  {self.name} (offset in composite_field {relative_offset})' )
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


    @staticmethod
    def create( field_type_map, field_definition, field_offset, endian='<' ):

        field_schema_name, field_name, field_semantic_type, field_since_version, field_definition_type_name, field_type = get_field_type_details( field_type_map, field_definition )

        composite_parts = [ ]
        if field_definition.get( 'offset', None ):
            field_offset = int( field_definition.get( 'offset', None ) )

        is_float_composite = False
        composite_field_length = 0
        for child in field_type[ 'children' ]:

            primitive_type_name = child[ 'primitive_type' ]
            primitive_type_fmt, primitive_type_size = fmt_and_size_by_type[ primitive_type_name ]
            unpack_fmt = f'{endian}{primitive_type_fmt}'
            child_since_version = int( child.get( 'since_version', '0' ) )

            constant = None
            optional = False
            if 'presence' in child:
                if child[ 'presence' ] == 'constant':
                    if primitive_type_name == 'char':
                        constant = str( child[ 'text' ] )
                    else:
                        constant = int( child[ 'text' ] )
                elif child[ 'presence' ] == 'optional':
                    optional = True

            null_value = None
            if 'null_value' in child:
                null_value = int( child[ 'null_value' ] )

            if child[ 'name' ] in ('mantissa', 'exponent'):
                is_float_composite = True

            composite_field = TypeMessageField( constant=constant, description=child.get( 'description', '' ), field_length=primitive_type_size, field_offset=field_offset, name=child[ 'name' ], null_value=null_value, optional=optional, schema_name=child[ 'name' ], semantic_type=field_semantic_type, since_version=child_since_version, unpack_fmt=unpack_fmt, )

            composite_field_length += primitive_type_size
            field_offset += primitive_type_size
            composite_parts.append( composite_field )

        # field_length of the composite field is the offset of the final item plus the size of final item
        field_length = composite_field_length
        field_id = field_definition[ 'id' ]
        field_description = field_definition.get( 'description', b'' )

        return CompositeMessageField( description=field_description, field_length=field_length, field_offset=field_offset, float_value=is_float_composite, id=field_id, name=field_name, schema_name=field_schema_name, parts=composite_parts, semantic_type=field_semantic_type, since_version=field_since_version, )
