#! /usr/bin/env python3

import logging
import xml.etree.ElementTree

from .aux import snake_case_from_CamelCase, parse_message_definitions, parse_type_definitions, fmt_and_size_by_type
from .field.comp import CompositeMessageField
from .field.enum import EnumMessageField
from .field.set import SetMessageField
from .field.type import TypeMessageField
from .mess import SBEMessage

log = logging.getLogger( 'sbedecoder.schema' )


class SBESchema:

    def __init__( self, xml_filename, include_message_size_header=False, use_description_as_message_name=False ):
        self.message_definitions = [ ]
        self.include_message_size_header = include_message_size_header
        self.use_description_as_message_name = use_description_as_message_name

        self.field_type_map = { }
        self.message_type_map = { }

        self.load( xml_filename )


    def create_type_field( self, field_definition, field_name, field_schema_name, field_semantic_type, field_since_version, field_type, message_type, offset, endian='<' ):

        primitive_type_ = field_type[ 'primitive_type' ]
        is_string_type = primitive_type_ == 'char' and 'length' in field_type and int( field_type[ 'length' ] ) > 1
        field_offset = offset
        if field_definition.get( 'offset', None ):
            field_offset = int( field_definition.get( 'offset', None ) )

        primitive_type_fmt, primitive_type_size = fmt_and_size_by_type[ primitive_type_ ]
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
                constant_prim_type = primitive_type_
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

        return TypeMessageField( name=field_name, schema_name=field_schema_name, id=field_id, description=field_description, unpack_fmt=unpack_fmt, field_offset=field_offset, field_length=field_length, null_value=null_value, constant=constant, optional=optional, is_string_type=is_string_type, semantic_type=field_semantic_type, since_version=field_since_version )


    def create_enum_field( self, field_definition, field_name, field_schema_name, field_semantic_type, field_since_version, field_type, message_type, offset, endian='<' ):

        encoding_type = field_type[ 'encoding_type' ]
        encoding_type_type = self.field_type_map[ encoding_type ]

        primitive_type_ = encoding_type_type[ 'primitive_type' ]
        primitive_type_fmt, primitive_type_size = fmt_and_size_by_type[ primitive_type_ ]
        field_offset = offset

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


    def create_set_field( self, field_definition, field_name, field_schema_name, field_semantic_type, field_since_version, field_type, message_type, offset, endian='<' ):

        field_offset = offset
        if field_definition.get( 'offset', None ):
            field_offset = int( field_definition.get( 'offset', None ) )

        encoding_type = field_type[ 'encoding_type' ]
        encoding_type_type = self.field_type_map[ encoding_type ]

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


    def create_composite_field( self, field_definition, field_name, field_schema_name, field_semantic_type, field_since_version, field_type, message_type, offset, endian='<' ):
        composite_parts = [ ]
        field_offset = offset
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


    def create_group( self, log_token, message_type, field_definition, field_offset ):

        dimension_type_name = field_definition[ 'dimension_type' ]
        dimension_type = self.field_type_map[ dimension_type_name ]
        children = dimension_type[ 'children' ]
        field_offset = self.create_fields_and_groups( f'{log_token} *', message_type, children, field_offset )

        children = field_definition[ 'children' ]
        field_offset = self.create_fields_and_groups( f'{log_token} *', message_type, children, field_offset )

        return field_offset


    def create_field( self, message_type, field_definition, field_offset, add_header_size=True ):

        field_schema_name = field_definition[ 'name' ]
        field_name = snake_case_from_CamelCase( field_schema_name )

        if 'primitive_type' in field_definition:
            field_definition_type_ = field_definition[ 'primitive_type' ]
        else:
            field_definition_type_ = field_definition[ 'type' ]

        field_type = self.field_type_map[ field_definition_type_ ]
        field_type_name = field_type[ 'type' ]

        field_semantic_type = field_definition.get( 'semantic_type', None )
        field_since_version = int( field_definition.get( 'since_version', 0 ) )

        if field_type_name == 'type':
            return self.create_type_field( field_definition, field_name, field_schema_name, field_semantic_type, field_since_version, field_type, message_type, field_offset )

        if field_type_name == 'enum':
            return self.create_enum_field( field_definition, field_name, field_schema_name, field_semantic_type, field_since_version, field_type, message_type, field_offset )

        if field_type_name == 'set':
            return self.create_set_field( field_definition, field_name, field_schema_name, field_semantic_type, field_since_version, field_type, message_type, field_offset )

        if field_type_name == 'composite':
            return self.create_composite_field( field_definition, field_name, field_schema_name, field_semantic_type, field_since_version, field_type, message_type, field_offset )


    def create_fields_and_groups( self, log_token, message_type, fields_and_groups_list, field_offset=None ):

        if field_offset is None:
            field_offset = message_type.header_size

        for field_definition in fields_and_groups_list:

            if 'dimension_type' in field_definition:
                field_offset = self.create_group( log_token, message_type, field_definition, field_offset )

            elif 'type' in field_definition:
                field = self.create_field( message_type, field_definition, field_offset )
                message_type.children.append( field )

                field_schema_name_id = f'{field_offset:<3}  {field.field_length:03}  {field.schema_name}/{field.id}'
                log.info( f'{log_token:<40}  {field_schema_name_id:<40}' )
                field_offset += field.field_length

        return field_offset


    def create_header( self, message_type, message_definition ):

        message_header_type = self.field_type_map[ 'messageHeader' ]
        header_field_types = message_header_type.get( 'children', [ ] )
        header_size = 0

        for header_field_type in header_field_types:
            primitive_type_fmt, primitive_type_size = fmt_and_size_by_type[ header_field_type[ 'primitive_type' ] ]
            header_field_type_name = header_field_type[ 'name' ]

            message_header_field = TypeMessageField( description=f'Header {header_field_type_name}', field_length=primitive_type_size, field_offset=header_size, name=snake_case_from_CamelCase( header_field_type_name ), schema_name=header_field_type_name, unpack_fmt=primitive_type_fmt, )
            message_type.children.append( message_header_field )
            setattr( message_type, message_header_field.name, message_header_field )

            message_name_id = f'{header_size:<3}  {message_header_field.field_length:03}  {message_type.schema_name}/{message_type.message_id}'
            log.info( f'{"header-field":<40}  {message_name_id:<40}  {header_field_type_name}' )

            header_size += primitive_type_size

        setattr( message_type, 'header_size', header_size )


    def create_message_type( self, message_definition, endian='<' ):
        log.info( '' )
        message_name = message_definition[ 'name' ]
        message_id = int( message_definition[ 'id' ] )
        message_type = type( message_name, (SBEMessage,), { 'message_id': message_id } )
        setattr( message_type, 'name', message_name )
        setattr( message_type, 'schema_name', message_name )
        setattr( message_type, 'children', [ ] )

        self.message_type_map[ message_id ] = message_type
        log_token = f'create-message-type  {message_name}/{message_id}'
        log.info( f'{log_token:<40}  {message_type}' )

        return message_type


    def create_message( self, message_definition ):

        message_type = self.create_message_type( message_definition )
        self.create_header( message_type, message_definition )

        fields_and_groups_list = message_definition.get( 'children', [ ] )
        self.create_fields_and_groups( 'create-fields-and-groups', message_type, fields_and_groups_list, field_offset=message_type.header_size )


    def load( self, xml_filename ):
        log.info( f'load-file {xml_filename}' )
        tree = xml.etree.ElementTree.parse( xml_filename )
        root = tree.getroot()

        self.field_type_map = parse_type_definitions( root )
        self.message_definitions = parse_message_definitions( root )

        for message_definition in self.message_definitions:
            self.create_message( message_definition )
