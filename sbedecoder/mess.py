#! /usr/bin/env python3

import logging
import struct

log = logging.getLogger( __name__ )


class SBEMessage:

    def __init__( self ):
        self.name = self.__class__.__name__
        self.buffer = b''
        self.offset = 0


    def __str__( self ):
        return f'{self.name}'


    def wrap( self, buffer, offset=0 ):
        self.buffer = buffer
        self.offset = offset

        for field in self.children:
            field_name_id = f'{field.schema_name}/{field.id}'
            # log.info( f'{"message-field-wrap":<40}  {offset:03}  {field.field_length:02x}  {field_name_id:<40}  {field.name}' )
            field.wrap( buffer, offset )
            offset += field.field_length

        # message_name_id = f'{self.name}/{self.message_id}'
        # log.info( f'{"message-fields-finish":<40}  {offset:03}  {message_name_id:<40}' )

        return offset


class SBEMessageFactory:

    def __init__( self, schema ):
        self.schema = schema


    def build( self, buffer, message_offset, template_id_offset ):
        template_id, = struct.unpack_from( '<H', buffer, template_id_offset )
        message_type = self.schema.message_type_map.get( template_id )
        message = message_type()
        message.wrap( buffer, message_offset )
        return message, len( buffer )
