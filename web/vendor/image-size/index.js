const MAX_INPUT_BYTES = 32 * 1024 * 1024;

function bytesFrom(input) {
  if (!(input instanceof Uint8Array)) {
    throw new TypeError("imageSize expects a Uint8Array or Buffer");
  }
  if (input.byteLength === 0 || input.byteLength > MAX_INPUT_BYTES) {
    throw new Error("Image metadata input is empty or exceeds 32 MiB");
  }
  return input;
}

function dimensions(type, width, height) {
  if (
    !Number.isSafeInteger(width) ||
    !Number.isSafeInteger(height) ||
    width <= 0 ||
    height <= 0
  ) {
    throw new Error(`Invalid ${type} image dimensions`);
  }
  return { type, width, height };
}

function isPrefix(bytes, values, offset = 0) {
  return values.every((value, index) => bytes[offset + index] === value);
}

function readUint16BE(bytes, offset) {
  return (bytes[offset] << 8) | bytes[offset + 1];
}

function readUint16LE(bytes, offset) {
  return bytes[offset] | (bytes[offset + 1] << 8);
}

function readUint24LE(bytes, offset) {
  return bytes[offset] | (bytes[offset + 1] << 8) | (bytes[offset + 2] << 16);
}

function readUint32BE(bytes, offset) {
  return (
    bytes[offset] * 0x1000000 +
    (bytes[offset + 1] << 16) +
    (bytes[offset + 2] << 8) +
    bytes[offset + 3]
  );
}

function readInt32LE(bytes, offset) {
  return (
    bytes[offset] |
    (bytes[offset + 1] << 8) |
    (bytes[offset + 2] << 16) |
    (bytes[offset + 3] << 24)
  );
}

function pngSize(bytes) {
  const signature = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a];
  if (bytes.length < 24 || !isPrefix(bytes, signature)) return null;
  return dimensions("png", readUint32BE(bytes, 16), readUint32BE(bytes, 20));
}

function gifSize(bytes) {
  if (bytes.length < 10) return null;
  const header = new TextDecoder("ascii").decode(bytes.subarray(0, 6));
  if (header !== "GIF87a" && header !== "GIF89a") return null;
  return dimensions("gif", readUint16LE(bytes, 6), readUint16LE(bytes, 8));
}

function jpegSize(bytes) {
  if (bytes.length < 4 || !isPrefix(bytes, [0xff, 0xd8])) return null;
  const startOfFrameMarkers = new Set([
    0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce,
    0xcf,
  ]);
  let offset = 2;

  while (offset + 3 < bytes.length) {
    if (bytes[offset] !== 0xff) {
      offset += 1;
      continue;
    }
    while (offset < bytes.length && bytes[offset] === 0xff) offset += 1;
    if (offset >= bytes.length) break;
    const marker = bytes[offset];
    offset += 1;
    if (marker === 0xd9 || marker === 0xda) break;
    if (marker === 0x01 || (marker >= 0xd0 && marker <= 0xd7)) continue;
    if (offset + 1 >= bytes.length) break;
    const segmentLength = readUint16BE(bytes, offset);
    if (segmentLength < 2 || offset + segmentLength > bytes.length) {
      throw new Error("Malformed JPEG segment length");
    }
    if (startOfFrameMarkers.has(marker)) {
      if (segmentLength < 7) throw new Error("Malformed JPEG start-of-frame segment");
      return dimensions(
        "jpg",
        readUint16BE(bytes, offset + 5),
        readUint16BE(bytes, offset + 3),
      );
    }
    offset += segmentLength;
  }
  throw new Error("JPEG dimensions were not found");
}

function webpSize(bytes) {
  if (
    bytes.length < 30 ||
    !isPrefix(bytes, [0x52, 0x49, 0x46, 0x46]) ||
    !isPrefix(bytes, [0x57, 0x45, 0x42, 0x50], 8)
  ) {
    return null;
  }
  const chunk = new TextDecoder("ascii").decode(bytes.subarray(12, 16));
  if (chunk === "VP8X") {
    return dimensions(
      "webp",
      readUint24LE(bytes, 24) + 1,
      readUint24LE(bytes, 27) + 1,
    );
  }
  if (chunk === "VP8 " && isPrefix(bytes, [0x9d, 0x01, 0x2a], 23)) {
    return dimensions(
      "webp",
      readUint16LE(bytes, 26) & 0x3fff,
      readUint16LE(bytes, 28) & 0x3fff,
    );
  }
  if (chunk === "VP8L" && bytes[20] === 0x2f) {
    const b0 = bytes[21];
    const b1 = bytes[22];
    const b2 = bytes[23];
    const b3 = bytes[24];
    return dimensions(
      "webp",
      1 + b0 + ((b1 & 0x3f) << 8),
      1 + (b1 >> 6) + (b2 << 2) + ((b3 & 0x0f) << 10),
    );
  }
  throw new Error("Unsupported or malformed WebP header");
}

function icoSize(bytes) {
  if (bytes.length < 22 || !isPrefix(bytes, [0x00, 0x00, 0x01, 0x00])) {
    return null;
  }
  const width = bytes[6] || 256;
  const height = bytes[7] || 256;
  return dimensions("ico", width, height);
}

function bmpSize(bytes) {
  if (bytes.length < 26 || !isPrefix(bytes, [0x42, 0x4d])) return null;
  return dimensions(
    "bmp",
    Math.abs(readInt32LE(bytes, 18)),
    Math.abs(readInt32LE(bytes, 22)),
  );
}

function svgSize(bytes) {
  const prefix = new TextDecoder("utf-8", { fatal: false }).decode(
    bytes.subarray(0, Math.min(bytes.length, 64 * 1024)),
  );
  const svgTag = prefix.match(/<svg\b[^>]*>/i)?.[0];
  if (!svgTag) return null;
  const width = svgTag.match(/\bwidth=["']\s*([0-9]+(?:\.[0-9]+)?)/i)?.[1];
  const height = svgTag.match(/\bheight=["']\s*([0-9]+(?:\.[0-9]+)?)/i)?.[1];
  if (width && height) return dimensions("svg", Math.round(Number(width)), Math.round(Number(height)));
  const viewBox = svgTag.match(
    /\bviewBox=["']\s*[-+0-9.]+[ ,]+[-+0-9.]+[ ,]+([0-9.]+)[ ,]+([0-9.]+)/i,
  );
  if (viewBox) {
    return dimensions("svg", Math.round(Number(viewBox[1])), Math.round(Number(viewBox[2])));
  }
  throw new Error("SVG dimensions require width/height or viewBox");
}

export function imageSize(input) {
  const bytes = bytesFrom(input);
  const parsers = [pngSize, gifSize, jpegSize, webpSize, icoSize, bmpSize, svgSize];
  for (const parser of parsers) {
    const result = parser(bytes);
    if (result) return result;
  }
  throw new Error("Unsupported image type; only PNG, JPEG, GIF, WebP, ICO, BMP, and SVG are allowed");
}
