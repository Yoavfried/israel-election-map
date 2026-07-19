from __future__ import annotations

import json
import struct
from dataclasses import dataclass
from typing import Any


GEOMETRY_TYPES = [
    "Point",
    "MultiPoint",
    "LineString",
    "MultiLineString",
    "Polygon",
    "MultiPolygon",
    "GeometryCollection",
]


@dataclass
class Reader:
    data: bytes
    position: int = 0

    def done(self) -> bool:
        return self.position >= len(self.data)

    def varint(self) -> int:
        value = 0
        shift = 0
        while True:
            byte = self.data[self.position]
            self.position += 1
            value |= (byte & 0x7F) << shift
            if byte < 0x80:
                return value
            shift += 7
            if shift > 70:
                raise ValueError("Invalid protobuf varint")

    def svarint(self) -> int:
        value = self.varint()
        return -(value + 1) // 2 if value & 1 else value // 2

    def field(self) -> tuple[int, int]:
        tag = self.varint()
        return tag >> 3, tag & 7

    def bytes_value(self) -> bytes:
        length = self.varint()
        end = self.position + length
        value = self.data[self.position:end]
        self.position = end
        return value

    def skip(self, wire_type: int) -> None:
        if wire_type == 0:
            self.varint()
        elif wire_type == 1:
            self.position += 8
        elif wire_type == 2:
            length = self.varint()
            self.position += length
        elif wire_type == 5:
            self.position += 4
        else:
            raise ValueError(f"Unsupported protobuf wire type: {wire_type}")


class PropertyDecoder:
    """Decode Geobuf attributes without executing the publisher's JavaScript."""

    def __init__(self) -> None:
        self.keys: list[str] = []
        self.values: list[Any] = []

    def decode(self, data: bytes) -> list[dict[str, Any]]:
        reader = Reader(data)
        features: list[dict[str, Any]] = []
        while not reader.done():
            field, wire = reader.field()
            if field == 1 and wire == 2:
                self.keys.append(reader.bytes_value().decode("utf-8"))
            elif field == 4 and wire == 2:
                features = self.feature_collection(Reader(reader.bytes_value()))
            elif field == 5 and wire == 2:
                features = [self.feature(Reader(reader.bytes_value()))]
            else:
                reader.skip(wire)
        return features

    def value(self, reader: Reader) -> Any:
        end = reader.position + reader.varint()
        value: Any = None
        while reader.position < end:
            field, wire = reader.field()
            if field == 1 and wire == 2:
                value = reader.bytes_value().decode("utf-8")
            elif field == 2 and wire == 1:
                value = struct.unpack(
                    "<d", reader.data[reader.position : reader.position + 8]
                )[0]
                reader.position += 8
            elif field == 3 and wire == 0:
                value = reader.varint()
            elif field == 4 and wire == 0:
                value = -reader.varint()
            elif field == 5 and wire == 0:
                value = bool(reader.varint())
            elif field == 6 and wire == 2:
                value = json.loads(reader.bytes_value().decode("utf-8"))
            else:
                reader.skip(wire)
        return value

    def properties(self, payload: bytes) -> dict[str, Any]:
        reader = Reader(payload)
        indexes: list[int] = []
        while not reader.done():
            indexes.append(reader.varint())
        if len(indexes) % 2:
            raise ValueError("Geobuf property index list has odd length")
        output = {
            self.keys[indexes[index]]: self.values[indexes[index + 1]]
            for index in range(0, len(indexes), 2)
        }
        self.values = []
        return output

    def feature_collection(self, reader: Reader) -> list[dict[str, Any]]:
        features: list[dict[str, Any]] = []
        while not reader.done():
            field, wire = reader.field()
            if field == 1 and wire == 2:
                features.append(self.feature(Reader(reader.bytes_value())))
            elif field == 13 and wire == 2:
                self.values.append(self.value(reader))
            elif field == 15 and wire == 2:
                self.properties(reader.bytes_value())
            else:
                reader.skip(wire)
        return features

    def feature(self, reader: Reader) -> dict[str, Any]:
        feature: dict[str, Any] = {"geometry_type": "", "properties": {}}
        while not reader.done():
            field, wire = reader.field()
            if field == 1 and wire == 2:
                feature["geometry_type"] = self.geometry_type(
                    Reader(reader.bytes_value())
                )
            elif field in {11, 12}:
                if wire == 2:
                    feature["id"] = reader.bytes_value().decode("utf-8")
                elif wire == 0:
                    feature["id"] = reader.svarint()
                else:
                    reader.skip(wire)
            elif field == 13 and wire == 2:
                self.values.append(self.value(reader))
            elif field == 14 and wire == 2:
                feature["properties"] = self.properties(reader.bytes_value())
            elif field == 15 and wire == 2:
                feature.update(self.properties(reader.bytes_value()))
            else:
                reader.skip(wire)
        return feature

    def geometry_type(self, reader: Reader) -> str:
        geometry_type = ""
        while not reader.done():
            field, wire = reader.field()
            if field == 1 and wire == 0:
                type_index = reader.varint()
                geometry_type = GEOMETRY_TYPES[type_index]
            elif field == 13 and wire == 2:
                self.values.append(self.value(reader))
            elif field == 15 and wire == 2:
                self.properties(reader.bytes_value())
            else:
                reader.skip(wire)
        return geometry_type


def decode_geobuf_properties(data: bytes) -> list[dict[str, Any]]:
    return PropertyDecoder().decode(data)
