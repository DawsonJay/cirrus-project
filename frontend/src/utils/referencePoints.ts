import { ReferencePoint } from './coordinateTransform';

/**
 * Reference points for Canada map calibration
 * These are the 23 manually calibrated points with actual pixel coordinates on 800x600 SVG
 * 
 * IMPORTANT: These coordinates are manually calibrated and should be preserved.
 * Use the RecalibrationOverlay component to adjust these points if needed.
 */
export const normalizedReferencePoints: Record<string, ReferencePoint> = {
  capecolumbia: { x: 527, y: 27, name: "Cape Columbia", lat: 83.111, lon: -69.958 },
  windsor: { x: 466, y: 568, name: "Windsor", lat: 42.3149, lon: -83.0364 },
  toronto: { x: 482, y: 558, name: "Toronto", lat: 43.7, lon: -79.4 },
  vancouver: { x: 277, y: 520, name: "Vancouver", lat: 49.2827, lon: -123.1207 },
  capespear: { x: 607, y: 530, name: "Cape Spear", lat: 47.517, lon: -52.617 },
  montreal: { x: 517, y: 544, name: "Montreal", lat: 45.502, lon: -73.567 },
  calgary: { x: 321, y: 505, name: "Calgary", lat: 51.0447, lon: -114.0719 },
  halifax: { x: 556, y: 552, name: "Halifax", lat: 44.6488, lon: -63.5752 },
  whitehorse: { x: 222, y: 428, name: "Whitehorse", lat: 60.7212, lon: -135.0568 },
  iqaluit: { x: 533, y: 396, name: "Iqaluit", lat: 63.7467, lon: -68.517 },
  stjohns: { x: 608, y: 527, name: "St. John's", lat: 47.5615, lon: -52.7126 },
  princerupert: { x: 242, y: 482, name: "Prince Rupert", lat: 54.3, lon: -130.3 },
  resolute: { x: 410, y: 246, name: "Resolute", lat: 74.7, lon: -94.8 },
  tuktoyaktuk: { x: 232, y: 324, name: "Tuktoyaktuk", lat: 69.4, lon: -133 },
  saskatoon: { x: 352, y: 497, name: "Saskatoon", lat: 52.1579, lon: -106.6702 },
  thunderbay: { x: 439, y: 524, name: "Thunder Bay", lat: 48.3809, lon: -89.2477 },
  victoria: { x: 276, y: 527, name: "Victoria", lat: 48.4284, lon: -123.3656 },
  fredericton: { x: 542, y: 544, name: "Fredericton", lat: 45.9636, lon: -66.6431 },
  inuvik: { x: 228, y: 340, name: "Inuvik", lat: 68.3607, lon: -133.723 },
  alert: { x: 564, y: 51, name: "Alert", lat: 82.5018, lon: -62.3481 },
  churchill: { x: 413, y: 442, name: "Churchill", lat: 58.768, lon: -94.17 },
  yellowknife: { x: 318, y: 409, name: "Yellowknife", lat: 62.454, lon: -114.372 },
  winnipeg: { x: 399, y: 515, name: "Winnipeg", lat: 49.895, lon: -97.138 },
};
