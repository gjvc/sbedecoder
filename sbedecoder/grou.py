#! /usr/bin/env python3

import logging

log = logging.getLogger( __name__ )

#
# class SBERepeatingGroupContainer:
#
#     def __init__( self, block_length_field=None, dimension_size=None, fields=None, groups=None, id=None, name=None, num_in_group_field=None, schema_name=None, since_version=0 ):
#         self.buffer = b''
#         self.offset = 0
#         self.relative_offset = 0
#
#         self.id = id
#         self.name = name
#         self.schema_name = schema_name
#         self.since_version = since_version
#
#         self.dimension_size = dimension_size
#         self.block_length_field = block_length_field
#         self.num_in_group_field = num_in_group_field
#         self._repeating_groups = [ ]
#
#         self.fields = fields or [ ]
#         self.groups = groups or [ ]
#
#
#     @property
#     def num_groups( self ):
#         return len( self._repeating_groups )
#
#
#     @property
#     def repeating_groups( self ):
#         for group in self._repeating_groups:
#             group.wrap()
#             yield group
#
#
#     def __getitem__( self, index ):
#         group = self._repeating_groups[ index ]
#         group.wrap()
#         return group
#
#
#     def wrap( self, buffer, offset, relative_offset ):
#         # log.info( f'{"wrap":<40} {offset:03}  {"":3}  {"":3}  {self.name}' )
#
#         self.buffer = buffer
#         self.offset = offset
#         self.relative_offset = relative_offset
#
#         # log.info( f'about to wrap block_length_field in {self.name}, msg_offset {offset}, relative_offset {relative_offset}' )
#         self.block_length_field.wrap( buffer, offset )
#         block_length = self.block_length_field.value
#
#         self.num_in_group_field.wrap( buffer, offset )
#         num_instances = self.num_in_group_field.value
#
#         name_id = f'{self.schema_name}/{self.id}'
#         if num_instances == 0:
#             log.info( f'{"group-container-wrap":<40}  {offset:03}  {self.dimension_size:<3}  {name_id:<40}  dimension_size={self.dimension_size}, num_instances={num_instances}' )
#             return self.dimension_size
#
#         self._repeating_groups = [ ]
#
#         repeated_group_offset = relative_offset + self.dimension_size
#         nested_groups_length = 0
#
#         for i in range( num_instances ):
#
#             relative_offset = repeated_group_offset + nested_groups_length
#             rg = SBERepeatingGroup( buffer, offset, relative_offset, self.name, self.schema_name, self.fields )
#             self._repeating_groups.append( rg )
#
#             repeated_group_offset += block_length
#             for nested_group in self.groups:
#                 # log.info( f'about to wrap nested_group {nested_group} {nested_group.name} within rg {self.name}' )
#                 group_length = nested_group.wrap( buffer, offset, relative_offset )
#                 repeated_group_offset += group_length
#
#                 for nested_repeating_group in nested_group._repeating_groups:
#                     rg.add_subgroup( nested_repeating_group )
#
#         size = self.dimension_size + (num_instances * block_length) + nested_groups_length
#         return size
#
#
# class SBERepeatingGroup:
#
#     def __init__( self, msg_buffer, msg_offset, relative_offset, name, schema_name, fields ):
#         self.buffer = msg_buffer
#         self.offset = msg_offset
#         self.relative_offset = relative_offset
#         self.fields = fields
#         self._groups = [ ]
#         self.name = name
#         self.schema_name = schema_name
#
#         for field in fields:
#             setattr( self, field.name, field )
#
#
#     def add_subgroup( self, subgroup ):
#         if not hasattr( self, subgroup.name ):
#             setattr( self, subgroup.name, [ subgroup ] )
#         else:
#             getattr( self, subgroup.name ).append( subgroup )
#         self._groups.append( subgroup )
#
#
#     @property
#     def groups( self ):
#         for group in self._groups:
#             group.wrap()
#             yield group
#
#
#     def wrap( self, relative_offset=0 ):
#         log.info( f'{"wrap":<40}  {self.offset:3}  {self.name}' )
#         bytes_decoded = 0
#         for field in self.fields:
#             # log.info( f'about to wrap field {field} {field.name} within group {self.name}' )
#             field.wrap( self.buffer, self.offset, relative_offset=self.relative_offset )
#         return bytes_decoded
