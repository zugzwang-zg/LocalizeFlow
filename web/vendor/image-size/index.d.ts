export interface ImageDimensions {
  width: number;
  height: number;
  type: "bmp" | "gif" | "ico" | "jpg" | "png" | "svg" | "webp";
}

export function imageSize(input: Uint8Array): ImageDimensions;
