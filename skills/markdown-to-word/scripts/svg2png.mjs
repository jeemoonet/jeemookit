#!/usr/bin/env node
/**
 * Render SVG to PNG via headless Chromium (supports CJK text in SVG <text> elements).
 * Usage: node svg2png.mjs <input.svg> <output.png>
 */
import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { dirname, resolve } from "path";
import puppeteer from "puppeteer";

const [inputSvg, outputPng] = process.argv.slice(2);
if (!inputSvg || !outputPng) {
  console.error("Usage: node svg2png.mjs <input.svg> <output.png>");
  process.exit(1);
}

const svgPath = resolve(inputSvg);
const pngPath = resolve(outputPng);
const svgContent = readFileSync(svgPath, "utf8");

function parseDimensions(content) {
  const viewBox = content.match(/viewBox=["']([^"']+)["']/);
  if (viewBox) {
    const parts = viewBox[1].trim().split(/[\s,]+/).map(Number);
    if (parts.length === 4 && parts[2] > 0 && parts[3] > 0) {
      return { width: Math.ceil(parts[2]), height: Math.ceil(parts[3]) };
    }
  }
  const width = content.match(/\bwidth=["']([\d.]+)/);
  const height = content.match(/\bheight=["']([\d.]+)/);
  if (width && height) {
    return {
      width: Math.ceil(Number(width[1])),
      height: Math.ceil(Number(height[1])),
    };
  }
  return { width: 820, height: 480 };
}

const { width, height } = parseDimensions(svgContent);

const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html, body {
    width: ${width}px;
    height: ${height}px;
    overflow: hidden;
    background: #fff;
  }
  svg {
    display: block;
    font-family: "Microsoft YaHei", "????", "SimHei", "SimSun", "PingFang SC",
      "Noto Sans CJK SC", sans-serif;
  }
  svg text, svg tspan {
    font-family: inherit;
  }
</style>
</head>
<body>${svgContent}</body>
</html>`;

const browser = await puppeteer.launch({
  headless: true,
  args: ["--no-sandbox", "--disable-setuid-sandbox", "--font-render-hinting=none"],
});

try {
  const page = await browser.newPage();
  await page.setViewport({
    width,
    height,
    deviceScaleFactor: 2,
  });
  await page.setContent(html, { waitUntil: "load" });
  await page.evaluate(() => document.fonts.ready);
  const pngBuffer = await page.screenshot({
    type: "png",
    clip: { x: 0, y: 0, width, height },
    omitBackground: false,
  });
  mkdirSync(dirname(pngPath), { recursive: true });
  writeFileSync(pngPath, pngBuffer);
} finally {
  await browser.close();
}
