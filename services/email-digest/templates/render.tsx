import { mkdirSync, writeFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

import { render } from "@react-email/render";
import DigestEmail, { DigestTemplateData } from "./DigestEmail.js";

const cardBaseStyle =
  "background:#F8FAFF;border-radius:20px;border:1px solid #BFDBFE;padding:24px;margin-bottom:16px;";
const projectTitleStyle = "font-size:18px;color:#3B82F6;margin:0 0 12px 0;font-weight:600;";
const statStyle =
  "display:flex;align-items:center;gap:10px;font-size:15px;color:#1F2937;margin:6px 0;font-weight:500;";

const iconStyle = "font-size:18px;line-height:1;";
const iconMessage = `<span aria-hidden="true" style="${iconStyle}">✉️</span>`;
const iconDocument = `<span aria-hidden="true" style="${iconStyle}">📄</span>`;

const sampleProjectSections = `
  <div style="${cardBaseStyle}">
    <p style="${projectTitleStyle}">Downtown Highrise Acquisition</p>
    <p style="${statStyle}">${iconMessage}<span><strong>2</strong> new messages (1 mentioned you)</span></p>
    <p style="${statStyle}">${iconDocument}<span><strong>1</strong> new document uploaded</span></p>
  </div>
  <div style="${cardBaseStyle}">
    <p style="${projectTitleStyle}">Seaside Retail Portfolio</p>
    <p style="${statStyle}">${iconMessage}<span><strong>1</strong> new message</span></p>
  </div>
  <div style="${cardBaseStyle}">
    <p style="${projectTitleStyle}">Mesa Industrial Expansion</p>
    <p style="${statStyle}">${iconDocument}<span><strong>2</strong> closing checklists updated</span></p>
  </div>
`;

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function main() {
const useSampleData = process.env.USE_SAMPLE_DATA === "true";

const sampleData: DigestTemplateData = {
  previewText: "3 updates across Downtown Highrise",
  userName: "Cody Field",
  digestDateLabel: "November 27, 2025",
  ctaUrl: "https://capmatch.com/dashboard",
  managePrefsUrl: "https://capmatch.com/settings/notifications",
  projectSectionsHtml: sampleProjectSections,
};

const html = await render(
  <DigestEmail {...(useSampleData ? sampleData : {})} />,
  {
    pretty: true,
  }
);

  const distDir = join(__dirname, "dist");
  mkdirSync(distDir, { recursive: true });

  const outputPath = join(distDir, "digest-template.html");
  writeFileSync(outputPath, html, { encoding: "utf-8" });

  console.log(`Digest template rendered to ${outputPath}`);
}

main().catch((err) => {
  console.error("Failed to render digest template:", err);
  process.exit(1);
});

