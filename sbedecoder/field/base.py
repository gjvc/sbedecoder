#! /usr/bin/env python3

import logging

log = logging.getLogger( __name__ )


class SBEMessageField:

    def __init__( self ):
        self.buffer = None
        self.description = None
        self.field_offset = 0
        self.id = None
        self.name = None
        self.offset = 0
        self.schema_name = None
        self.unpack_fmt = None


    def wrap( self, buffer, offset=0 ):
        self.buffer = buffer
        self.offset = offset


    @property
    def value( self ):
        return None


    @property
    def raw_value( self ):
        return None

    # def __str__( self, raw=False ):
    #     if raw and self.value != self.raw_value:
    #         return f"{self.name}: {str( self.value )} ({str( self.raw_value )})"
    #     return f"{self.name}: {str( self.value )}"
