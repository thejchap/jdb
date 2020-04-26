# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

import peer_server_pb2 as peer__server__pb2


class PeerServerStub(object):
    """Missing associated documentation comment in .proto file"""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.MembershipStateSync = channel.unary_unary(
                '/PeerServer/MembershipStateSync',
                request_serializer=peer__server__pb2.MembershipState.SerializeToString,
                response_deserializer=peer__server__pb2.MembershipState.FromString,
                )
        self.MembershipPing = channel.unary_unary(
                '/PeerServer/MembershipPing',
                request_serializer=peer__server__pb2.Empty.SerializeToString,
                response_deserializer=peer__server__pb2.Empty.FromString,
                )
        self.MembershipPingReq = channel.unary_unary(
                '/PeerServer/MembershipPingReq',
                request_serializer=peer__server__pb2.Empty.SerializeToString,
                response_deserializer=peer__server__pb2.Empty.FromString,
                )


class PeerServerServicer(object):
    """Missing associated documentation comment in .proto file"""

    def MembershipStateSync(self, request, context):
        """Missing associated documentation comment in .proto file"""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def MembershipPing(self, request, context):
        """Missing associated documentation comment in .proto file"""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def MembershipPingReq(self, request, context):
        """Missing associated documentation comment in .proto file"""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_PeerServerServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'MembershipStateSync': grpc.unary_unary_rpc_method_handler(
                    servicer.MembershipStateSync,
                    request_deserializer=peer__server__pb2.MembershipState.FromString,
                    response_serializer=peer__server__pb2.MembershipState.SerializeToString,
            ),
            'MembershipPing': grpc.unary_unary_rpc_method_handler(
                    servicer.MembershipPing,
                    request_deserializer=peer__server__pb2.Empty.FromString,
                    response_serializer=peer__server__pb2.Empty.SerializeToString,
            ),
            'MembershipPingReq': grpc.unary_unary_rpc_method_handler(
                    servicer.MembershipPingReq,
                    request_deserializer=peer__server__pb2.Empty.FromString,
                    response_serializer=peer__server__pb2.Empty.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'PeerServer', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class PeerServer(object):
    """Missing associated documentation comment in .proto file"""

    @staticmethod
    def MembershipStateSync(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/PeerServer/MembershipStateSync',
            peer__server__pb2.MembershipState.SerializeToString,
            peer__server__pb2.MembershipState.FromString,
            options, channel_credentials,
            call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def MembershipPing(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/PeerServer/MembershipPing',
            peer__server__pb2.Empty.SerializeToString,
            peer__server__pb2.Empty.FromString,
            options, channel_credentials,
            call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def MembershipPingReq(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/PeerServer/MembershipPingReq',
            peer__server__pb2.Empty.SerializeToString,
            peer__server__pb2.Empty.FromString,
            options, channel_credentials,
            call_credentials, compression, wait_for_ready, timeout, metadata)
