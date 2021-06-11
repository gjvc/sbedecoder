#! /usr/bin/env python3

import logging
import struct

log = logging.getLogger( __name__ )


class SBEMessageFactory:

    def __init__( self, schema ):
        self.schema = schema


    def build( self, buffer, message_offset, template_id_offset ):
        template_id, = struct.unpack_from( '<H', buffer, template_id_offset )
        message_type = self.schema.message_type_map.get( template_id )
        message = message_type()
        message.wrap( buffer, message_offset )
        return message, len( buffer )
