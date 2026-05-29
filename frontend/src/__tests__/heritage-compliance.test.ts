import { describe, it, expect } from "vitest";
import * as fs from "node:fs";
import * as path from "node:path";

/**
 * Static analysis tests for Heritage theme compliance.
 * These tests scan source files to ensure no dark theme remnants remain.
 */

const SRC_DIR = path.resolve(__dirname, "..");

const SCAN_DIRS = [
  path.join(SRC_DIR, "app", "(dashboard)"),
  path.join(SRC_DIR, "components"),
];

function getTsxFiles(dirs: string[]): string[] {
  const files: string[] = [];
  for (const dir of dirs) {
    if (!fs.existsSync(dir)) continue;
    const entries = fs.readdirSync(dir, { recursive: true, encoding: "utf-8" });
    for (const entry of entries) {
      if (entry.endsWith(".tsx")) {
        files.push(path.join(dir, entry));
      }
    }
  }
  return files;
}

describe("Feature: dashboard-ui-redesign, Property 4: No dark mode variant classes", () => {
  it("should not contain any dark: variant classes in dashboard pages and components", () => {
    const files = getTsxFiles(SCAN_DIRS);
    expect(files.length).toBeGreaterThan(0);

    const darkClassPattern = /dark:[a-z]/;
    const violations: { file: string; line: number; content: string }[] = [];

    for (const filePath of files) {
      const content = fs.readFileSync(filePath, "utf-8");
      const lines = content.split("\n");

      for (let i = 0; i < lines.length; i++) {
        if (darkClassPattern.test(lines[i])) {
          violations.push({
            file: path.relative(SRC_DIR, filePath),
            line: i + 1,
            content: lines[i].trim(),
          });
        }
      }
    }

    if (violations.length > 0) {
      const report = violations
        .map((v) => `  ${v.file}:${v.line} → ${v.content}`)
        .join("\n");
      expect.fail(
        `Found ${violations.length} dark: variant class(es):\n${report}`,
      );
    }
  });
});

describe("Feature: dashboard-ui-redesign, Property 5: No hardcoded dark theme colors", () => {
  it("should not contain any hardcoded dark theme hex color values", () => {
    const files = getTsxFiles(SCAN_DIRS);
    expect(files.length).toBeGreaterThan(0);

    const forbiddenColors = [
      "#08090a",
      "#12141a",
      "#0f1011",
      "#161718",
      "#23252a",
      "#323334",
      "#383b3f",
      "#e4f222",
      "#f7f8f8",
      "#8a8f98",
      "#62666d",
    ];

    // Build a case-insensitive regex that matches any of the forbidden hex values
    const pattern = new RegExp(
      forbiddenColors.map((c) => c.replace("#", "#")).join("|"),
      "i",
    );

    const violations: {
      file: string;
      line: number;
      matched: string;
      content: string;
    }[] = [];

    for (const filePath of files) {
      const content = fs.readFileSync(filePath, "utf-8");
      const lines = content.split("\n");

      for (let i = 0; i < lines.length; i++) {
        const match = lines[i].match(pattern);
        if (match) {
          violations.push({
            file: path.relative(SRC_DIR, filePath),
            line: i + 1,
            matched: match[0],
            content: lines[i].trim(),
          });
        }
      }
    }

    if (violations.length > 0) {
      const report = violations
        .map((v) => `  ${v.file}:${v.line} [${v.matched}] → ${v.content}`)
        .join("\n");
      expect.fail(
        `Found ${violations.length} hardcoded dark theme color(s):\n${report}`,
      );
    }
  });
});
