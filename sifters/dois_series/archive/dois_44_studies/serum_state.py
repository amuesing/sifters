"""Read and write Serum 2's plugin state as pedalboard exposes it (`plugin.raw_state`).

Xfer does not document this format; it was read from Serum 2.1.5's own state and from
.SerumPreset files, and `serum_render.py` refuses any other version rather than guess.

  raw_state  = b'VC2!' + uint32 length + XML (UTF-8, null-terminated)       JUCE's wrapper
  XML        = <VST3PluginState><IComponent>N.base64</IComponent><IEditController>...
  IComponent = JUCE's base64 of an Xfer container:
               b'XferJson\\0' + uint64 header length + JSON header
               + uint32 CBOR length + uint32 2 + zstd(CBOR)
  header['hash'] is the MD5 of the zstd bytes.

A .SerumPreset file is the same Xfer container without JUCE's wrapper. Inside, the patch is
a map of modules; the ones `serum_render.py` touches:

  Oscillator0.WTOsc0.relativePathToWT   the table, relative to Serum's Tables folder
  Oscillator0.WTOsc0.numFrames          its length in samples (frames x 2048)
  Oscillator0.plainParams               kParamPitchTrack (0 = off), kParamOctave,
                                        kParamCoarsePit (semitones), kParamVolume
  ModSlotN                              source [code, 0]; destModuleTypeString,
                                        destModuleID, destModuleParamID,
                                        destModuleParamName; plainParams.kParamAmount
  tuningName, tuningData                a loaded .tun: its name, and its bytes as a
                                        list of integers
"""
import hashlib
import json
import re
import struct

import cbor2
import zstandard

ALPHABET = ".ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+"


def juce_decode(text):
    size, data = text.split('.', 1)
    size = int(size)
    out = bytearray(size)
    pos = 0
    for ch in data:
        value = ALPHABET.index(ch)
        for i in range(6):
            if (value >> i) & 1:
                index = (pos + i) // 8
                if index < size:
                    out[index] |= 1 << ((pos + i) % 8)
        pos += 6
    return bytes(out)


def juce_encode(data):
    bits = int.from_bytes(data, 'little')
    chars = ((len(data) * 8) + 5) // 6
    return f"{len(data)}." + ''.join(ALPHABET[(bits >> (6 * i)) & 63] for i in range(chars))


def read_xfer(blob):
    if blob[:9] != b'XferJson\x00':
        raise ValueError("not an Xfer container")
    size = struct.unpack('<Q', blob[9:17])[0]
    header = json.loads(blob[17:17 + size])
    rest = blob[17 + size:]
    _, marker = struct.unpack('<II', rest[:8])
    data = cbor2.loads(zstandard.ZstdDecompressor().decompress(rest[8:], max_output_size=10**9))
    return header, marker, data


def write_xfer(header, marker, data):
    payload = cbor2.dumps(data)
    compressed = zstandard.ZstdCompressor(level=3).compress(payload)
    header = dict(header, hash=hashlib.md5(compressed).hexdigest())
    text = json.dumps(header, separators=(',', ':')).encode()
    return (b'XferJson\x00' + struct.pack('<Q', len(text)) + text
            + struct.pack('<II', len(payload), marker) + compressed)


def read_state(raw):
    """(xml, header, marker, patch) from `plugin.raw_state`."""
    if raw[:4] != b'VC2!':
        raise ValueError("not a JUCE plugin state")
    length = struct.unpack('<I', raw[4:8])[0]
    xml = raw[8:8 + length].decode('utf-8')
    blob = juce_decode(re.search(r'<IComponent>(.*?)</IComponent>', xml, re.S).group(1))
    header, marker, data = read_xfer(blob)
    return xml, header, marker, data


def write_state(xml, header, marker, data):
    blob = write_xfer(header, marker, data)
    xml = re.sub(r'<IComponent>.*?</IComponent>',
                 lambda m: f'<IComponent>{juce_encode(blob)}</IComponent>', xml, flags=re.S)
    text = xml.encode('utf-8')
    return b'VC2!' + struct.pack('<I', len(text)) + text + b'\x00'
