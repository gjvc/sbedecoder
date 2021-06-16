#! /usr/bin/env python3

import logging
import struct

log = logging.getLogger( 'tinysbe' )


class SBEMessage:

    def __init__( self ):
        self.name = self.__class__.__name__
        self.buffer = b''
        self.offset = 0


    def __str__( self ):
        return f'{self.name}'


    def wrap( self, buffer, offset ):

        self.buffer = buffer
        self.offset = offset

        # field_name_id = f'{item.message_type_name}/{item.id}'
        # log.info( f'{"message-item-wrap":<40}  {offset:03}  {item.field_length:02x}  {field_name_id:<40}  {item.name}' )

        for item in self.children:
            item.wrap( buffer, offset )
            offset += item.field_length

        # message_name_id = f'{self.name}/{self.message_id}'
        # log.info( f'{"message-fields-finish":<40}  {offset:03}  {message_name_id:<40}' )

        return offset


class SBEMessageFactory:

    def __init__( self, schema ):
        self.schema = schema


    def build( self, buffer, message_offset, template_id_offset ):
        template_id, = struct.unpack_from( '<H', buffer, template_id_offset )
        message_type = self.schema.message_type_by_id.get( template_id )
        message = message_type()
        count = message.wrap( buffer, message_offset )
        return message, count
