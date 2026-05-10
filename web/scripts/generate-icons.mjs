import sharp from 'sharp';
import { readFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dir = dirname(fileURLToPath(import.meta.url));
const svgPath = resolve(__dir, '../public/icon.svg');
const svg = readFileSync(svgPath);

const sizes = [
  { size: 192, filename: 'pwa-192.png' },
  { size: 512, filename: 'pwa-512.png' },
  { size: 180, filename: 'apple-touch-icon.png' },
];

for (const { size, filename } of sizes) {
  const out = resolve(__dir, `../public/${filename}`);
  await sharp(svg).resize(size, size).png().toFile(out);
  console.log(`Generated ${filename} (${size}x${size})`);
}

console.log('Icons generated.');
